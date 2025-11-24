PS C:\\Users\\boydp\\Desktop\\midas\_V2\_v0.4.7.9\_working> Invoke-WebRequest "http://127.0.0.1:5001/patch?dry\_run=1\&scenario=B" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{ "require\_macd\_rise": true, "macd\_rise\_bars": 2 }'





StatusCode        : 200

StatusDescription : OK

Content           : {"applied\_fields":\[],"dry\_run":true,"params\_after":{"macd\_rise\_bars":2,"require\_macd\_rise":true,"to

&nbsp;                   p":5},"params\_before":{"macd\_rise\_bars":2,"require\_macd\_rise":true,"top":5},"scenario":"B"}



RawContent        : HTTP/1.1 200 OK

&nbsp;                   Access-Control-Allow-Origin: http://127.0.0.1:5173

&nbsp;                   Vary: Origin

&nbsp;                   Connection: close

&nbsp;                   Content-Length: 191

&nbsp;                   Content-Type: application/json

&nbsp;                   Date: Mon, 24 Nov 2025 13:40:08 GMT

&nbsp;                   Server: ...

Forms             : {}

Headers           : {\[Access-Control-Allow-Origin, http://127.0.0.1:5173], \[Vary, Origin], \[Connection, close],

&nbsp;                   \[Content-Length, 191]...}

Images            : {}

InputFields       : {}

Links             : {}

ParsedHtml        : mshtml.HTMLDocumentClass

RawContentLength  : 191







PS C:\\Users\\boydp\\Desktop\\midas\_V2\_v0.4.7.9\_working>

PS C:\\Users\\boydp\\Desktop\\midas\_V2\_v0.4.7.9\_working> Invoke-WebRequest "http://127.0.0.1:5001/patch?apply=1\&scenario=B" -Method POST -Headers @{ "Content-Type" = "application/json" } -Body '{ "require\_macd\_rise": false, "macd\_rise\_bars": 3 }'





StatusCode        : 200

StatusDescription : OK

Content           : {"applied\_fields":\["require\_macd\_rise","macd\_rise\_bars"],"backup\_file":"scenarios.2025-11-24T13-43-

&nbsp;                   45.bak.json","dry\_run":false,"params\_after":{"macd\_rise\_bars":3,"require\_macd\_rise":false,"top":5},

&nbsp;                   "p...

RawContent        : HTTP/1.1 200 OK

&nbsp;                   Access-Control-Allow-Origin: http://127.0.0.1:5173

&nbsp;                   Vary: Origin

&nbsp;                   Connection: close

&nbsp;                   Content-Length: 284

&nbsp;                   Content-Type: application/json

&nbsp;                   Date: Mon, 24 Nov 2025 13:43:45 GMT

&nbsp;                   Server: ...

Forms             : {}

Headers           : {\[Access-Control-Allow-Origin, http://127.0.0.1:5173], \[Vary, Origin], \[Connection, close],

&nbsp;                   \[Content-Length, 284]...}

Images            : {}

InputFields       : {}

Links             : {}

ParsedHtml        : mshtml.HTMLDocumentClass

RawContentLength  : 284



