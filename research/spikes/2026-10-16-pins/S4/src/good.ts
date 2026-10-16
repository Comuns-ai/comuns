export function add(a: number, b: number): number {
  return a + b;
}

export function first<T>(xs: readonly T[]): T | undefined {
  return xs[0];
}

async function work(): Promise<number> {
  return Promise.resolve(1);
}

export async function run(): Promise<void> {
  work(); // deliberate floating promise
  await work();
}
