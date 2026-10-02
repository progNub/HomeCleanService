import { copyFile, cp, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import * as sass from 'sass';

const root = new URL('../', import.meta.url);
const output = new URL('cms/static/cms/dist/', root);
await mkdir(output, { recursive: true });
const css = sass.compile(fileURLToPath(new URL('cms/static/cms/scss/main.scss', root)), {
  loadPaths: [fileURLToPath(new URL('node_modules', root))],
  style: 'compressed',
  // Bootstrap 5 still uses the Sass APIs deprecated before Bootstrap 6.
  silenceDeprecations: ['import', 'global-builtin', 'color-functions', 'if-function'],
});
await writeFile(new URL('main.css', output), css.css);
await copyFile(
  new URL('node_modules/bootstrap/dist/js/bootstrap.bundle.min.js', root),
  new URL('bootstrap.bundle.min.js', output),
);
await copyFile(
  new URL('node_modules/bootstrap/dist/js/bootstrap.bundle.min.js.map', root),
  new URL('bootstrap.bundle.min.js.map', output),
);
await copyFile(
  new URL('node_modules/bootstrap-icons/font/bootstrap-icons.min.css', root),
  new URL('bootstrap-icons.css', output),
);
await cp(
  new URL('node_modules/bootstrap-icons/font/fonts/', root),
  new URL('fonts/', output),
  { recursive: true },
);
console.log('Built CSS, Bootstrap JS and icon fonts in cms/static/cms/dist');
