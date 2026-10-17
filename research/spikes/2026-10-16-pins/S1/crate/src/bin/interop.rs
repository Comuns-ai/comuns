//! S3 interop driver (native only). Bytes are passed through files.
//!   interop server-config <out.bin>                      (TEST_IKM-derived KeyConfig)
//!   interop server <plain|chunked> <req.bin> <resp.bin>  (decapsulate, answer)
//!   interop client <plain|chunked> <config.bin> <req.out> <resp.in>
//!       (encapsulate, write req.out, wait up to 30 s for resp.in, decapsulate)

#[cfg(not(target_arch = "wasm32"))]
fn main() {
    if let Err(e) = native::run() {
        eprintln!("RUST ERROR: {e}");
        std::process::exit(1);
    }
}

#[cfg(target_arch = "wasm32")]
fn main() {}

#[cfg(not(target_arch = "wasm32"))]
mod native {
    use std::{fs, path::Path, thread::sleep, time::Duration};

    use bhttp::Mode;
    use comuns_crypto_spike::{
        SharedBuf, TEST_IKM, derived_server_config, parse_bhttp, poll_now, sample_request,
        sample_response,
    };
    use futures::{AsyncReadExt, AsyncWriteExt};
    use ohttp::{ClientRequest, Server};

    fn hex(b: &[u8]) -> String {
        b.iter().map(|x| format!("{x:02x}")).collect()
    }

    fn describe(bytes: &[u8]) -> Result<String, String> {
        let m = parse_bhttp(bytes)?;
        let c = m.control();
        let head = if let Some(s) = c.status() {
            format!("status={}", s.code())
        } else {
            format!(
                "{} {}://{}{}",
                String::from_utf8_lossy(c.method().unwrap_or_default()),
                String::from_utf8_lossy(c.scheme().unwrap_or_default()),
                String::from_utf8_lossy(c.authority().unwrap_or_default()),
                String::from_utf8_lossy(c.path().unwrap_or_default()),
            )
        };
        Ok(format!(
            "{head} body={:?}",
            String::from_utf8_lossy(m.content())
        ))
    }

    fn wait_for(p: &Path) -> Result<Vec<u8>, String> {
        for _ in 0..300 {
            if let Ok(b) = fs::read(p)
                && !b.is_empty()
            {
                return Ok(b);
            }
            sleep(Duration::from_millis(100));
        }
        Err(format!("timeout waiting for {}", p.display()))
    }

    pub fn run() -> Result<(), String> {
        let a: Vec<String> = std::env::args().collect();
        let e = |s: &'static str| move |x: ohttp::Error| format!("{s}: {x}");
        match a.get(1).map(String::as_str) {
            Some("server-config") => {
                let cfg = derived_server_config(&TEST_IKM)?;
                let enc = Server::new(cfg).map_err(e("server"))?.config().encode().map_err(e("encode"))?;
                fs::write(&a[2], &enc).map_err(|x| x.to_string())?;
                println!("rust server-config {}B {}", enc.len(), hex(&enc));
            }
            Some("server") => {
                let chunked = a[2] == "chunked";
                let server = Server::new(derived_server_config(&TEST_IKM)?).map_err(e("server"))?;
                let req = fs::read(&a[3]).map_err(|x| x.to_string())?;
                println!("rust server got {}B header={}", req.len(), hex(&req[..7.min(req.len())]));
                let body = b"hello from rust gateway";
                let out = if chunked {
                    let mut sreq = server.decapsulate_stream(&req[..]);
                    let mut pt = Vec::new();
                    poll_now(sreq.read_to_end(&mut pt))?.map_err(|x| format!("read req: {x}"))?;
                    println!("rust server decapsulated (chunked): {}", describe(&pt)?);
                    let sink = SharedBuf::default();
                    let mut w = sreq.response(sink.clone()).map_err(e("response"))?;
                    let resp = sample_response(Mode::IndeterminateLength, body)?;
                    let half = resp.len() / 2;
                    poll_now(w.write_all(&resp[..half]))?.map_err(|x| x.to_string())?;
                    poll_now(w.write_all(&resp[half..]))?.map_err(|x| x.to_string())?;
                    poll_now(w.close())?.map_err(|x| x.to_string())?;
                    sink.take()
                } else {
                    let (pt, sresp) = server.decapsulate(&req).map_err(e("decapsulate"))?;
                    println!("rust server decapsulated: {}", describe(&pt)?);
                    let resp = sample_response(Mode::KnownLength, body)?;
                    sresp.encapsulate(&resp).map_err(e("encapsulate resp"))?
                };
                fs::write(&a[4], &out).map_err(|x| x.to_string())?;
                println!("rust server wrote {}B response", out.len());
            }
            Some("client") => {
                let chunked = a[2] == "chunked";
                let cfg = fs::read(&a[3]).map_err(|x| x.to_string())?;
                println!("rust client config {}B {}", cfg.len(), hex(&cfg));
                let client = ClientRequest::from_encoded_config(&cfg).map_err(e("client cfg"))?;
                if chunked {
                    let req = sample_request(Mode::IndeterminateLength)?;
                    let sink = SharedBuf::default();
                    let mut creq = client.encapsulate_stream(sink.clone()).map_err(e("stream"))?;
                    poll_now(creq.write_all(&req))?.map_err(|x| x.to_string())?;
                    poll_now(creq.close())?.map_err(|x| x.to_string())?;
                    let enc = sink.take();
                    fs::write(&a[4], &enc).map_err(|x| x.to_string())?;
                    println!("rust client wrote {}B chunked request", enc.len());
                    let resp = wait_for(Path::new(&a[5]))?;
                    let mut r = creq.response(&resp[..]).map_err(e("response"))?;
                    let mut pt = Vec::new();
                    poll_now(r.read_to_end(&mut pt))?.map_err(|x| format!("read resp: {x}"))?;
                    println!("rust client decapsulated (chunked): {}", describe(&pt)?);
                } else {
                    let req = sample_request(Mode::KnownLength)?;
                    let (enc, cresp) = client.encapsulate(&req).map_err(e("encapsulate"))?;
                    fs::write(&a[4], &enc).map_err(|x| x.to_string())?;
                    println!("rust client wrote {}B request", enc.len());
                    let resp = wait_for(Path::new(&a[5]))?;
                    let pt = cresp.decapsulate(&resp).map_err(e("decapsulate resp"))?;
                    println!("rust client decapsulated: {}", describe(&pt)?);
                }
            }
            _ => return Err("usage: see source".into()),
        }
        Ok(())
    }
}
