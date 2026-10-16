use alloy::primitives::{address, b256, keccak256, FixedBytes, B256, U256};
use alloy::signers::local::PrivateKeySigner;
use alloy::signers::SignerSync;
use alloy::sol;
use alloy::sol_types::{Eip712Domain, SolStruct};

sol! {
    struct Voucher {
        bytes32 sessionId;
        uint64 seq;
        uint256 cumulativeWei;
        uint64 inputTokens;
        uint64 outputTokens;
        bytes32 outputCommitment;
        bool r#final;
    }
}

fn main() {
    // public Foundry/anvil test key (anvil key #0); never use for value
    let key: B256 = b256!("ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80");
    let signer = PrivateKeySigner::from_bytes(&key).unwrap();
    let domain = Eip712Domain::new(
        Some("SessionEscrow".into()),
        Some("1".into()),
        Some(U256::from(421614u64)),
        Some(address!("000000000000000000000000000000000000dEaD")),
        None,
    );
    let z = FixedBytes::<32>::ZERO;
    let vs = [
        Voucher { sessionId: FixedBytes::repeat_byte(0x11), seq: 1, cumulativeWei: U256::from(1000000000000000u64), inputTokens: 128, outputTokens: 256, outputCommitment: z, r#final: false },
        Voucher { sessionId: FixedBytes::repeat_byte(0xab), seq: 42, cumulativeWei: "123456789012345678901234567890".parse().unwrap(), inputTokens: 4096, outputTokens: 8192, outputCommitment: FixedBytes::repeat_byte(0xcd), r#final: true },
        Voucher { sessionId: FixedBytes::repeat_byte(0xff), seq: u64::MAX, cumulativeWei: U256::MAX, inputTokens: u64::MAX, outputTokens: u64::MAX, outputCommitment: FixedBytes::repeat_byte(0x01), r#final: true },
    ];
    println!("signer {}", signer.address());
    println!("encodeType {}", Voucher::eip712_encode_type());
    println!("typeHash {}", keccak256(Voucher::eip712_encode_type().as_bytes()));
    println!("domainSeparator {}", domain.separator());
    for v in &vs {
        let h = v.eip712_signing_hash(&domain);
        let sig = signer.sign_hash_sync(&h).unwrap();
        println!("structHash {}", v.eip712_hash_struct());
        println!("signingHash {}", h);
        println!("signature 0x{}", alloy::primitives::hex::encode(sig.as_bytes()));
    }
}
