import { hashDomain, hashStruct, hashTypedData, recoverTypedDataAddress, keccak256, toHex } from 'viem';
import { privateKeyToAccount, signTypedData } from 'viem/accounts';

// public Foundry/anvil test key (anvil key #0); never use for value
const TEST_KEY = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80';
const domain = { name: 'SessionEscrow', version: '1', chainId: 421614n, verifyingContract: '0x000000000000000000000000000000000000dEaD' };
const types = { Voucher: [
  { name: 'sessionId', type: 'bytes32' }, { name: 'seq', type: 'uint64' },
  { name: 'cumulativeWei', type: 'uint256' }, { name: 'inputTokens', type: 'uint64' },
  { name: 'outputTokens', type: 'uint64' }, { name: 'outputCommitment', type: 'bytes32' },
  { name: 'final', type: 'bool' } ] };
const Z = '0x' + '00'.repeat(32);
const vouchers = [
  { sessionId: '0x' + '11'.repeat(32), seq: 1n, cumulativeWei: 1000000000000000n, inputTokens: 128n, outputTokens: 256n, outputCommitment: Z, final: false },
  { sessionId: '0x' + 'ab'.repeat(32), seq: 42n, cumulativeWei: 123456789012345678901234567890n, inputTokens: 4096n, outputTokens: 8192n, outputCommitment: '0x' + 'cd'.repeat(32), final: true },
  { sessionId: '0x' + 'ff'.repeat(32), seq: 18446744073709551615n, cumulativeWei: 2n ** 256n - 1n, inputTokens: 18446744073709551615n, outputTokens: 18446744073709551615n, outputCommitment: '0x' + '01'.repeat(32), final: true },
];
const account = privateKeyToAccount(TEST_KEY);
const typeHash = keccak256(toHex('Voucher(bytes32 sessionId,uint64 seq,uint256 cumulativeWei,uint64 inputTokens,uint64 outputTokens,bytes32 outputCommitment,bool final)'));
const domainTypes = { EIP712Domain: [{name:'name',type:'string'},{name:'version',type:'string'},{name:'chainId',type:'uint256'},{name:'verifyingContract',type:'address'}] };
const out = { signer: account.address, typeHash, domainSeparator: hashDomain({ domain, types: domainTypes }), vouchers: [] };
for (const v of vouchers) {
  const message = v;
  const signingHash = hashTypedData({ domain, types, primaryType: 'Voucher', message });
  const structHash = hashStruct({ data: message, primaryType: 'Voucher', types });
  const signature = await signTypedData({ privateKey: TEST_KEY, domain, types, primaryType: 'Voucher', message });
  const recovered = await recoverTypedDataAddress({ domain, types, primaryType: 'Voucher', message, signature });
  out.vouchers.push({ structHash, signingHash, signature, recovered, recoveredMatches: recovered === account.address });
}
console.log(JSON.stringify(out, null, 2));
