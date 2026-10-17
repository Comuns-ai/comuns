/// Test (b) with the fixed suite (ChaCha20-Poly1305). S9: no wasm guard; the patched
/// ohttp sizes the response-nonce buffer for max(Nn, Nk) = 32.
pub fn roundtrip_b() -> Result<String, String> {
    roundtrip_b_suite(Aead::ChaCha20Poly1305)
}

fn varint(len: usize) -> Vec<u8> {
    match len {
        0..64 => vec![len as u8],
        64..16384 => (0x4000u16 | len as u16).to_be_bytes().to_vec(),
        _ => panic!("chunk too long for this test"),
    }
}

/// Read `r` to the end with a fixed-size output buffer. Returns the plaintext read so far
/// and the outcome. A large buffer exercises ohttp's `read_into_output` fast path, a buffer
/// smaller than one chunk exercises the buffered path.
fn read_loop<R: AsyncRead + Unpin>(r: &mut R, bufsize: usize) -> (Vec<u8>, Result<(), String>) {
    let mut out = Vec::new();
    let mut buf = vec![0u8; bufsize];
    loop {
        match poll_now(r.read(&mut buf)) {
            Err(e) => return (out, Err(e)),
            Ok(Err(e)) => return (out, Err(e.to_string())),
            Ok(Ok(0)) => return (out, Ok(())),
            Ok(Ok(n)) => out.extend_from_slice(&buf[..n]),
        }
    }
}

/// Test (c): a chunked response that carries a zero-length NON-final chunk must be rejected
/// (draft-ietf-ohai-chunked-ohttp-08 §6: equivalent to a decryption error), not read as EOF.
///
/// The patched ohttp writer can no longer emit such a chunk, so the response is built by hand
/// as the gateway would: the TEST server key is re-derived from `TEST_IKM`, the HPKE receiver
/// context is set up from the client's real chunked request, and the response key/nonce are
/// derived as in RFC 9458 §4.4 with the "message/bhttp chunked response" exporter label.
/// A positive control (the same construction without the empty chunk) must decrypt.
pub fn roundtrip_c() -> Result<String, String> {
    use ::hpke::{
        Deserializable, OpModeR,
        aead::ChaCha20Poly1305 as HpkeChaCha,
        kdf::HkdfSha256,
        kem::{Kem as _, X25519HkdfSha256},
        setup_receiver,
    };
    use chacha20poly1305::{
        ChaCha20Poly1305,
        aead::{Aead as _, KeyInit, Nonce, Payload},
    };

    let server = Server::new(derived_server_config(&TEST_IKM)?).map_err(err("server"))?;
    let encoded = server.config().encode().map_err(err("encode cfg"))?;
    let client = ClientRequest::from_encoded_config(&encoded).map_err(err("client cfg"))?;
    let sink = SharedBuf::default();
    let mut creq = client
        .encapsulate_stream(sink.clone())
        .map_err(err("encapsulate_stream"))?;
    poll_now(creq.write_all(b"req"))?.map_err(err("write req"))?;
    poll_now(creq.close())?.map_err(err("close req"))?;
    let enc_req = sink.take();

    // Gateway side, by hand. Request header = key_id(1) kem(2) kdf(2) aead(2), then enc (32).
    let header = &enc_req[..7];
    let enc = &enc_req[7..39];
    let mut info = b"message/bhttp chunked request".to_vec();
    info.push(0);
    info.extend_from_slice(header);
    let (sk, _pk) = X25519HkdfSha256::derive_keypair(&TEST_IKM);
    let encapped =
        <X25519HkdfSha256 as ::hpke::Kem>::EncappedKey::from_bytes(enc).map_err(err("enc"))?;
    let ctx = setup_receiver::<HpkeChaCha, HkdfSha256, X25519HkdfSha256>(
        &OpModeR::Base,
        &sk,
        &encapped,
        &info,
    )
    .map_err(err("setup_receiver"))?;
    let mut secret = [0u8; 32]; // max(Nn, Nk) for ChaCha20-Poly1305
    ctx.export(b"message/bhttp chunked response", &mut secret)
        .map_err(err("export"))?;

    let build = |chunks: &[&[u8]]| -> Result<Vec<u8>, String> {
        let response_nonce = [0x5a_u8; 32];
        let mut salt = enc.to_vec();
        salt.extend_from_slice(&response_nonce);
        let hk = hkdf::Hkdf::<sha2::Sha256>::new(Some(&salt), &secret);
        let mut key = [0u8; 32];
        let mut iv = [0u8; 12];
        hk.expand(b"key", &mut key).map_err(err("expand key"))?;
        hk.expand(b"nonce", &mut iv).map_err(err("expand nonce"))?;
        let cipher = ChaCha20Poly1305::new_from_slice(&key).map_err(err("key"))?;
        let seal = |seq: u64, aad: &[u8], pt: &[u8]| -> Result<Vec<u8>, String> {
            let mut n = iv;
            for (i, b) in n.iter_mut().rev().take(8).enumerate() {
                *b ^= (seq >> (8 * i)) as u8;
            }
            let n = Nonce::<ChaCha20Poly1305>::try_from(&n[..]).map_err(err("nonce"))?;
            cipher
                .encrypt(&n, Payload { msg: pt, aad })
                .map_err(err("seal"))
        };
        let mut out = response_nonce.to_vec();
        for (i, c) in chunks.iter().enumerate() {
            let ct = seal(i as u64, b"", c)?;
            out.extend(varint(ct.len()));
            out.extend(ct);
        }
        out.extend(varint(0));
        out.extend(seal(chunks.len() as u64, b"final", b"")?);
        Ok(out)
    };

    // Positive control: the hand-built response decrypts on both read paths.
    let good = build(&[b"one", b"two"])?;
    for bufsize in [1024, 8] {
        let mut r = creq.response(&good[..]).map_err(err("client resp"))?;
        let (pt, res) = read_loop(&mut r, bufsize);
        if res.is_err() || pt != b"onetwo" {
            return Err(format!(
                "c: positive control failed (buf {bufsize}): {res:?} {pt:?}"
            ));
        }
    }

    // Injected: one, <empty non-final>, two, final.
    let bad = build(&[b"one", b"", b"two"])?;
    let mut seen = Vec::new();
    for bufsize in [1024, 8] {
        let mut r = creq.response(&bad[..]).map_err(err("client resp"))?;
        let (pt, res) = read_loop(&mut r, bufsize);
        match res {
            Err(e) => seen.push(format!(
                "buf {bufsize}: rejected with error {e:?} after {:?}",
                String::from_utf8_lossy(&pt)
            )),
            Ok(()) => {
                return Err(format!(
                    "c: zero-length non-final chunk ACCEPTED (buf {bufsize}): read ended cleanly with plaintext {:?}",
                    String::from_utf8_lossy(&pt)
                ));
            }
        }
    }
    Ok(format!(
        "c: zero-length non-final chunk rejected ({} B response; positive control ok; {})",
        bad.len(),
        seen.join("; ")
    ))
}

/// Test (d): `write(&[])` on a chunked writer emits no bytes (draft-08 §6: a sender MUST NOT
/// send a zero-length non-final chunk). Checked on the client request writer and on the
/// gateway response writer, both before and after the first data write.
pub fn roundtrip_d() -> Result<String, String> {
    let server = Server::new(server_config()?).map_err(err("server"))?;
    let encoded = server.config().encode().map_err(err("encode cfg"))?;
    let client = ClientRequest::from_encoded_config(&encoded).map_err(err("client cfg"))?;

    fn empty_write<W: AsyncWrite + Unpin>(
        w: &mut W,
        s: &SharedBuf,
        log: &mut Vec<(Result<usize, String>, usize)>,
    ) {
        let before = s.0.borrow().len();
        let n = poll_now(w.write(&[])).and_then(|r| r.map_err(|e| e.to_string()));
        let after = s.0.borrow().len();
        log.push((n, after - before));
    }

    let mut emitted = Vec::new();
    let req_sink = SharedBuf::default();
    let mut creq = client
        .encapsulate_stream(req_sink.clone())
        .map_err(err("stream"))?;
    empty_write(&mut creq, &req_sink, &mut emitted);
    poll_now(creq.write_all(b"req"))?.map_err(err("write req"))?;
    empty_write(&mut creq, &req_sink, &mut emitted);
    poll_now(creq.close())?.map_err(err("close req"))?;
    let enc_req = req_sink.take();

    let mut sreq = server.decapsulate_stream(&enc_req[..]);
    let mut dec_req = Vec::new();
    poll_now(sreq.read_to_end(&mut dec_req))?.map_err(err("read req"))?;
    if dec_req != b"req" {
        return Err("d: request mismatch".into());
    }
    let resp_sink = SharedBuf::default();
    let mut sresp = sreq
        .response(resp_sink.clone())
        .map_err(err("response"))?;
    empty_write(&mut sresp, &resp_sink, &mut emitted);
    poll_now(sresp.write_all(b"one"))?.map_err(err("write"))?;
    empty_write(&mut sresp, &resp_sink, &mut emitted);
    poll_now(sresp.write_all(b"two"))?.map_err(err("write"))?;
    poll_now(sresp.close())?.map_err(err("close"))?;
    let enc_resp = resp_sink.take();

    for (i, (n, bytes)) in emitted.iter().enumerate() {
        if *n != Ok(0) || *bytes != 0 {
            return Err(format!(
                "d: empty write #{i} returned {n:?} and emitted {bytes} B"
            ));
        }
    }
    let mut r = creq.response(&enc_resp[..]).map_err(err("client resp"))?;
    let mut out = Vec::new();
    poll_now(r.read_to_end(&mut out))?.map_err(err("read resp"))?;
    if out != b"onetwo" {
        return Err(format!("d: response mismatch {out:?}"));
    }
    Ok(format!(
        "d: 4 empty writes (client req before/after data, gateway resp before/after data) returned Ok(0) and emitted 0 B; stream still decrypts ({} B resp)",
        enc_resp.len()
    ))
}

