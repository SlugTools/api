function promtpGo(value, argument, url) {
  let input = prompt(`➡️ Enter ${argument}: (or use example)`, value);
  if (input.trim() == "") {
    console.log(input);
    return;
  }
  // TODO: urllib.parse.quote_plus imitation not functioning
  window.open(`${url}${encodeURIComponent(input)}`);
}
