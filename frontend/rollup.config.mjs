import nodeResolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";
import typescript from "@rollup/plugin-typescript";

export default {
  input: "src/index.ts",
  output: {
    file: "../custom_components/curenergia/frontend/curenergia.js",
    format: "es",
    inlineDynamicImports: true,
  },
  plugins: [
    nodeResolve(),
    typescript({ tsconfig: "./tsconfig.json", include: ["src/**/*.ts"], noEmit: false, outDir: undefined, declaration: false }),
    terser({ format: { comments: false } }),
  ],
};
