//! Throwaway spike: RFC 9458 OHTTP (and chunked OHTTP) round trips with the fixed
//! Comuns suite DHKEM(X25519, HKDF-SHA256) / HKDF-SHA256 / ChaCha20-Poly1305,
//! natively and on wasm32-unknown-unknown.

use std::{
    cell::RefCell,
    future::Future,
    io::{Cursor, Result as IoResult},
    pin::{Pin, pin},
    rc::Rc,
    task::{Context, Poll, Waker},
};

use bhttp::{Message, Mode, StatusCode};
use futures::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};
use ohttp::{
    ClientRequest, KeyConfig, Server, SymmetricSuite,
    hpke::{Aead, Kdf, Kem},
};

/// TEST key id.
pub const KEY_ID: u8 = 1;
/// TEST input keying material for a deterministic server key (spike only).
pub const TEST_IKM: [u8; 32] = [0x42; 32];

/// The one fixed suite: X25519 / HKDF-SHA256 / ChaCha20-Poly1305.
pub fn fixed_suite() -> Vec<SymmetricSuite> {
    vec![SymmetricSuite::new(Kdf::HkdfSha256, Aead::ChaCha20Poly1305)]
}

/// Server KeyConfig with the fixed suite and a random key.
pub fn server_config() -> Result<KeyConfig, String> {
    KeyConfig::new(KEY_ID, Kem::X25519Sha256, fixed_suite()).map_err(|e| e.to_string())
}

/// Server KeyConfig with the fixed suite, derived from `ikm` (deterministic, TEST only).
pub fn derived_server_config(ikm: &[u8]) -> Result<KeyConfig, String> {
    KeyConfig::derive(KEY_ID, Kem::X25519Sha256, fixed_suite(), ikm).map_err(|e| e.to_string())
}

fn err<E: std::fmt::Display>(ctx: &str) -> impl FnOnce(E) -> String + '_ {
    move |e| format!("{ctx}: {e}")
}

/// A small BHTTP request (known-length).
pub fn sample_request(mode: Mode) -> Result<Vec<u8>, String> {
    let mut m = Message::request(
        b"POST".to_vec(),
        b"https".to_vec(),
        b"gateway.example".to_vec(),
        b"/v1/infer".to_vec(),
    );
    m.put_header("content-type", "application/json");
    m.write_content(br#"{"prompt":"hello"}"#);
    let mut out = Vec::new();
    m.write_bhttp(mode, &mut out).map_err(err("bhttp write req"))?;
    Ok(out)
}

/// A small BHTTP response.
pub fn sample_response(mode: Mode, body: &[u8]) -> Result<Vec<u8>, String> {
    let mut m = Message::response(StatusCode::try_from(200u16).map_err(err("status"))?);
    m.put_header("content-type", "text/plain");
    m.write_content(body);
    let mut out = Vec::new();
    m.write_bhttp(mode, &mut out).map_err(err("bhttp write resp"))?;
    Ok(out)
}

pub fn parse_bhttp(bytes: &[u8]) -> Result<Message, String> {
    let mut c = Cursor::new(bytes);
    Message::read_bhttp::<Cursor<&[u8]>, Cursor<&[u8]>>(&mut c).map_err(err("bhttp read"))
}

/// Test (a): RFC 9458 non-chunked round trip.
pub fn roundtrip_a() -> Result<String, String> {
    let server = Server::new(server_config()?).map_err(err("server"))?;
    let encoded = server.config().encode().map_err(err("encode cfg"))?;

    let req = sample_request(Mode::KnownLength)?;
    let client = ClientRequest::from_encoded_config(&encoded).map_err(err("client cfg"))?;
    let (enc_req, client_resp) = client.encapsulate(&req).map_err(err("encapsulate"))?;

    // header: key_id(1) kem(2) kdf(2) aead(2) = 01 0020 0001 0003
    if enc_req[..7] != [0x01, 0x00, 0x20, 0x00, 0x01, 0x00, 0x03] {
        return Err(format!("unexpected header {:02x?}", &enc_req[..7]));
    }

    let (dec_req, server_resp) = server.decapsulate(&enc_req).map_err(err("decapsulate"))?;
    if dec_req != req {
        return Err("request mismatch".into());
    }
    let m = parse_bhttp(&dec_req)?;
    if m.control().path() != Some(&b"/v1/infer"[..]) || m.content() != br#"{"prompt":"hello"}"# {
        return Err("bhttp request content mismatch".into());
    }

    let resp = sample_response(Mode::KnownLength, b"world")?;
    let enc_resp = server_resp.encapsulate(&resp).map_err(err("encap resp"))?;
    let dec_resp = client_resp.decapsulate(&enc_resp).map_err(err("decap resp"))?;
    if dec_resp != resp {
        return Err("response mismatch".into());
    }
    Ok(format!(
        "a: RFC9458 ok (cfg {}B, req {}B, resp {}B)",
        encoded.len(),
        enc_req.len(),
        enc_resp.len()
    ))
}

/// Drive a future that never truly blocks (all I/O is in memory) to completion
/// with a single poll. Avoids an executor (thread parking) so it also works on wasm32.
pub fn poll_now<F: Future>(f: F) -> Result<F::Output, String> {
    let mut f = pin!(f);
    let mut cx = Context::from_waker(Waker::noop());
    match f.as_mut().poll(&mut cx) {
        Poll::Ready(v) => Ok(v),
        Poll::Pending => Err("future unexpectedly pending".into()),
    }
}

/// In-memory AsyncWrite sink that can be read while the writer is still alive.
#[derive(Clone, Default)]
pub struct SharedBuf(pub Rc<RefCell<Vec<u8>>>);

impl SharedBuf {
    pub fn take(&self) -> Vec<u8> {
        std::mem::take(&mut self.0.borrow_mut())
    }
}

impl AsyncWrite for SharedBuf {
    fn poll_write(self: Pin<&mut Self>, _: &mut Context<'_>, b: &[u8]) -> Poll<IoResult<usize>> {
        self.0.borrow_mut().extend_from_slice(b);
        Poll::Ready(Ok(b.len()))
    }
    fn poll_flush(self: Pin<&mut Self>, _: &mut Context<'_>) -> Poll<IoResult<()>> {
        Poll::Ready(Ok(()))
    }
    fn poll_close(self: Pin<&mut Self>, _: &mut Context<'_>) -> Poll<IoResult<()>> {
        Poll::Ready(Ok(()))
    }
}

async fn read_some<R: AsyncRead + Unpin>(r: &mut R) -> IoResult<Vec<u8>> {
    let mut buf = vec![0u8; 1 << 15];
    let n = r.read(&mut buf).await?;
    buf.truncate(n);
    Ok(buf)
}

/// Test (b): chunked (draft-ietf-ohai-chunked-ohttp) request + response round trip,
/// with a 3-frame response; also checks that the first frame decrypts from a prefix
/// of the encapsulated response (incremental delivery).
pub fn roundtrip_b_suite(aead: Aead) -> Result<String, String> {
    let cfg = KeyConfig::new(
        KEY_ID,
        Kem::X25519Sha256,
        vec![SymmetricSuite::new(Kdf::HkdfSha256, aead)],
    )
    .map_err(err("cfg"))?;
    let server = Server::new(cfg).map_err(err("server"))?;
    let encoded = server.config().encode().map_err(err("encode cfg"))?;
    let client = ClientRequest::from_encoded_config(&encoded).map_err(err("client cfg"))?;

    let req = sample_request(Mode::IndeterminateLength)?;
    let req_sink = SharedBuf::default();
    let mut creq = client
        .encapsulate_stream(req_sink.clone())
        .map_err(err("encapsulate_stream"))?;
    poll_now(creq.write_all(&req))?.map_err(err("write req"))?;
    poll_now(creq.close())?.map_err(err("close req"))?;
    let enc_req = req_sink.take();

    let mut sreq = server.clone().decapsulate_stream(&enc_req[..]);
    let mut dec_req = Vec::new();
    poll_now(sreq.read_to_end(&mut dec_req))?.map_err(err("read req"))?;
    if dec_req != req {
        return Err("chunked request mismatch".into());
    }
    parse_bhttp(&dec_req)?;

    let frames: [&[u8]; 3] = [b"frame-1;", b"frame-2;", b"frame-3."];
    let resp_sink = SharedBuf::default();
    let mut sresp = sreq.response(resp_sink.clone()).map_err(err("server response"))?;
    let mut lens = Vec::new();
    for f in frames {
        poll_now(sresp.write_all(f))?.map_err(err("write frame"))?;
        lens.push(resp_sink.0.borrow().len());
    }
    poll_now(sresp.close())?.map_err(err("close resp"))?;
    let enc_resp = resp_sink.take();

    // Incremental: only the nonce + first chunk available.
    let mut partial = creq.response(&enc_resp[..lens[0]]).map_err(err("client resp"))?;
    let first = poll_now(read_some(&mut partial))?.map_err(err("partial read"))?;
    if first != frames[0] {
        return Err(format!("incremental first frame mismatch: {first:?}"));
    }

    let mut cresp = creq.response(&enc_resp[..]).map_err(err("client resp"))?;
    let mut dec_resp = Vec::new();
    poll_now(cresp.read_to_end(&mut dec_resp))?.map_err(err("read resp"))?;
    if dec_resp != frames.concat() {
        return Err("chunked response mismatch".into());
    }

    // Truncation (missing final chunk) must be detected.
    let mut trunc = creq.response(&enc_resp[..lens[2]]).map_err(err("client resp"))?;
    let mut sink = Vec::new();
    let truncated_ok = poll_now(trunc.read_to_end(&mut sink))?.is_err();
    if !truncated_ok {
        return Err("truncated chunked response was accepted".into());
    }

    Ok(format!(
        "b[{aead:?}]: chunked ok (req {}B, resp {}B, 3 frames + final, incremental first frame ok, truncation rejected)",
        enc_req.len(),
        enc_resp.len()
    ))
}

/// Response nonce length per RFC 9458: max(Nn, Nk). ohttp 0.8.0's stream client
/// holds it in a `[u8; 16]` (stream.rs:244/743) and slices `[..entropy]` (stream.rs:775),
/// which panics for ChaCha20-Poly1305 (Nk = 32).
pub fn response_nonce_len(aead: Aead) -> usize {
    aead.n_n().max(aead.n_k())
}

/// Test (b) with the fixed suite (ChaCha20-Poly1305).
/// Native: runs it and converts a panic into an error. wasm32 (panic = abort): reports
/// the known upstream panic instead of trapping; `roundtrip_b_raw` runs it unguarded.
pub fn roundtrip_b() -> Result<String, String> {
    #[cfg(not(target_arch = "wasm32"))]
    {
        let prev = std::panic::take_hook();
        std::panic::set_hook(Box::new(|_| {}));
        let r = std::panic::catch_unwind(|| roundtrip_b_suite(Aead::ChaCha20Poly1305));
        std::panic::set_hook(prev);
        match r {
            Ok(r) => r,
            Err(p) => {
                let msg = p
                    .downcast_ref::<String>()
                    .cloned()
                    .or_else(|| p.downcast_ref::<&str>().map(|s| (*s).to_string()))
                    .unwrap_or_default();
                Err(format!(
                    "b[ChaCha20Poly1305]: PANIC in ohttp stream client: {msg}"
                ))
            }
        }
    }
    #[cfg(target_arch = "wasm32")]
    {
        let n = response_nonce_len(Aead::ChaCha20Poly1305);
        if n > 16 {
            return Err(format!(
                "b[ChaCha20Poly1305]: not run under wasm guard: ohttp 0.8.0 stream client nonce buffer is 16 bytes, suite needs {n} (panics natively at stream.rs:775)"
            ));
        }
        roundtrip_b_suite(Aead::ChaCha20Poly1305)
    }
}

/// Diagnostic only (NOT the fixed suite): chunked round trip with AES-128-GCM.
pub fn roundtrip_b_aes_diagnostic() -> Result<String, String> {
    roundtrip_b_suite(Aead::Aes128Gcm)
}

pub fn roundtrip_all() -> String {
    let a = roundtrip_a();
    let b = roundtrip_b();
    let diag = match roundtrip_b_aes_diagnostic() {
        Ok(d) => format!("diagnostic {d}"),
        Err(e) => format!("diagnostic FAIL {e}"),
    };
    match (a, b) {
        (Ok(a), Ok(b)) => format!("PASS {a}; {b}; {diag}"),
        (Ok(a), Err(b)) => format!("FAIL(b) {a}; {b}; {diag}"),
        (a, b) => format!("FAIL a={a:?} b={b:?}; {diag}"),
    }
}

#[cfg(target_arch = "wasm32")]
mod wasm {
    use wasm_bindgen::prelude::*;

    #[wasm_bindgen]
    pub fn roundtrip() -> String {
        super::roundtrip_all()
    }

    /// Runs chunked test (b) with ChaCha20-Poly1305 unguarded (expected to trap).
    #[wasm_bindgen]
    pub fn roundtrip_b_raw() -> String {
        match super::roundtrip_b_suite(super::Aead::ChaCha20Poly1305) {
            Ok(s) => format!("PASS {s}"),
            Err(e) => format!("FAIL {e}"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_a_rfc9458_roundtrip() {
        let r = roundtrip_a().unwrap();
        println!("{r}");
    }

    #[test]
    fn test_b_chunked_roundtrip() {
        let r = roundtrip_b().unwrap();
        println!("{r}");
    }

    #[test]
    fn test_b_aes128gcm_diagnostic() {
        let r = roundtrip_b_aes_diagnostic().unwrap();
        println!("{r}");
    }

    /// S3: draft-08 §6 says a receiver MUST treat a zero-length non-final chunk as a
    /// decryption error. Emit one (poll_write with empty input) and see what the
    /// ohttp 0.8.0 client does. AES-128-GCM because the ChaCha client path panics.
    #[test]
    fn test_s3_empty_nonfinal_chunk() {
        let cfg = KeyConfig::new(
            KEY_ID,
            Kem::X25519Sha256,
            vec![SymmetricSuite::new(Kdf::HkdfSha256, Aead::Aes128Gcm)],
        )
        .unwrap();
        let server = Server::new(cfg).unwrap();
        let encoded = server.config().encode().unwrap();
        let client = ClientRequest::from_encoded_config(&encoded).unwrap();
        let sink = SharedBuf::default();
        let mut creq = client.encapsulate_stream(sink.clone()).unwrap();
        poll_now(creq.write_all(b"req")).unwrap().unwrap();
        poll_now(creq.close()).unwrap().unwrap();
        let enc_req = sink.take();
        let mut sreq = server.decapsulate_stream(&enc_req[..]);
        let mut r = Vec::new();
        poll_now(sreq.read_to_end(&mut r)).unwrap().unwrap();
        let rs = SharedBuf::default();
        let mut sresp = sreq.response(rs.clone()).unwrap();
        poll_now(sresp.write_all(b"one")).unwrap().unwrap();
        let before = rs.0.borrow().len();
        let n = poll_now(sresp.write(&[])).unwrap().unwrap();
        let empty_chunk_bytes = rs.0.borrow().len() - before;
        poll_now(sresp.write_all(b"two")).unwrap().unwrap();
        poll_now(sresp.close()).unwrap().unwrap();
        let enc = rs.take();
        let mut cresp = creq.response(&enc[..]).unwrap();
        let mut out = Vec::new();
        let res = poll_now(cresp.read_to_end(&mut out)).unwrap();
        println!(
            "S3 empty non-final chunk: sender wrote {n} pt bytes as a {empty_chunk_bytes}-byte framed chunk; receiver result={:?} plaintext={:?}",
            res.as_ref().map_err(|e| e.to_string()),
            String::from_utf8_lossy(&out)
        );
    }

    #[test]
    fn test_all_summary() {
        let s = roundtrip_all();
        println!("{s}");
        assert!(s.starts_with("PASS"), "{s}");
    }
}
