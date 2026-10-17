use alloy::dyn_abi::eip712::TypedData;
use alloy::primitives::{b256, keccak256, B256};
use alloy::signers::local::PrivateKeySigner;
use alloy::signers::SignerSync;

fn main() {
    // public Foundry/anvil test key (anvil key #0); never use for value
    let key: B256 = b256!("ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80");
    let signer = PrivateKeySigner::from_bytes(&key).unwrap();
    let z = format!("0x{}", "00".repeat(32));
    let u256max = "115792089237316195423570985008687907853269984665640564039457584007913129639935";
    let u64max = "18446744073709551615";
    let msgs = [
        ("0x".to_string() + &"11".repeat(32), "1", "1000000000000000", "128", "256", z.clone(), false),
        ("0x".to_string() + &"ab".repeat(32), "42", "123456789012345678901234567890", "4096", "8192", "0x".to_string() + &"cd".repeat(32), true),
        ("0x".to_string() + &"ff".repeat(32), u64max, u256max, u64max, u64max, "0x".to_string() + &"01".repeat(32), true),
    ];
    println!("signer {}", signer.address());
    for (sid, seq, cw, it, ot, oc, fin) in msgs {
        let j = format!(r#"{{
 "types": {{
  "EIP712Domain": [{{"name":"name","type":"string"}},{{"name":"version","type":"string"}},{{"name":"chainId","type":"uint256"}},{{"name":"verifyingContract","type":"address"}}],
  "Voucher": [{{"name":"sessionId","type":"bytes32"}},{{"name":"seq","type":"uint64"}},{{"name":"cumulativeWei","type":"uint256"}},{{"name":"inputTokens","type":"uint64"}},{{"name":"outputTokens","type":"uint64"}},{{"name":"outputCommitment","type":"bytes32"}},{{"name":"final","type":"bool"}}]
 }},
 "primaryType": "Voucher",
 "domain": {{"name":"SessionEscrow","version":"1","chainId":"421614","verifyingContract":"0x000000000000000000000000000000000000dEaD"}},
 "message": {{"sessionId":"{sid}","seq":"{seq}","cumulativeWei":"{cw}","inputTokens":"{it}","outputTokens":"{ot}","outputCommitment":"{oc}","final":{fin}}}
}}"#);
        let td: TypedData = serde_json::from_str(&j).unwrap();
        let enc = td.encode_type().unwrap();
        println!("encodeType {enc}");
        println!("typeHash {}", keccak256(enc.as_bytes()));
        println!("domainSeparator {}", td.domain.separator());
        println!("structHash {}", td.hash_struct().unwrap());
        let h = td.eip712_signing_hash().unwrap();
        println!("signingHash {h}");
        println!("signature 0x{}", alloy::primitives::hex::encode(signer.sign_hash_sync(&h).unwrap().as_bytes()));
    }
}
