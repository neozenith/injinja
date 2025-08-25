# Diagrams

This folder contains the original MermaidJS Architecture Diagrams as `.mmd` files.

Recommend using the [VSCode Mermaid Preview Extension](https://marketplace.visualstudio.com/items?itemName=vstirbu.vscode-mermaid-preview) for live editting.

The `.png` files are updated with the [`mermaid.cli`](https://www.npmjs.com/package/@mermaid-js/mermaid-cli)

```sh
npx -p @mermaid-js/mermaid-cli mmdc
```

It is kept up to date with the following `Makefile` rule:

```makefile
diagrams/%.png: diagrams/%.mmd
	npx -p @mermaid-js/mermaid-cli mmdc --input $< --output $@ --theme default -backgroundColor transparent --scale 4

diag: $(patsubst %.mmd,%.png,$(wildcard diagrams/*.mmd))
```

Whilst there is support for templating and replacing the code blocks in a markdown file with SVGs:

```sh
mmdc -i readme.template.md -o readme.md
```

I'd rather create and embed the PNG for best compatability.
