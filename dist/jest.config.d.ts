export let preset: string;
export let testEnvironment: string;
export let roots: string[];
export let testMatch: string[];
export let transform: {
    '^.+\\.(ts|tsx)$': string;
};
export let collectCoverageFrom: string[];
export let moduleFileExtensions: string[];
export let testTimeout: number;
