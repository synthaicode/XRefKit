async function inlineSvg(host) {
  const source = host.dataset.inlineSvg;
  if (!source) return;
  const response = await fetch(source);
  if (!response.ok) return;
  const documentNode = new DOMParser().parseFromString(await response.text(), "image/svg+xml");
  const svg = documentNode.documentElement;
  if (svg.nodeName.toLowerCase() !== "svg") return;
  svg.removeAttribute("width");
  host.replaceChildren(document.importNode(svg, true));
}

for (const host of document.querySelectorAll("[data-inline-svg]")) {
  inlineSvg(host);
}
