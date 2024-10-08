https://browser.engineering/http.html

1-4 Entities. Implement support for the less-than (&lt;) and greater-than (&gt;) entities. These should be printed as < and >, respectively. For example, if the HTML response was &lt;div&gt;, the show method of your browser should print <div>. Entities allow web pages to include these special characters without the browser interpreting them as tags.

1-6 Keep-alive. Implement Exercise 1-1; however, do not send the Connection: close header. Instead, when reading the body from the socket, only read as many bytes as given in the Content-Length header and don’t close the socket afterward. Instead, save the socket, and if another request is made to the same socket reuse the same socket instead of creating a new one. This will speed up repeated requests to the same server, which is common.

1-7 Redirects. http://browser.engineering/redirect3

1-8 Caching. Typically, the same images, styles, and scripts are used on multiple pages; downloading them repeatedly is a waste. It’s generally valid to cache any HTTP response, as long as it was requested with GET and received a 200 response.Some other status codes like 301 and 404 can also be cached. Implement a cache in your browser and test it by requesting the same file multiple times. Servers control caches using the Cache-Control header. Add support for this header, specifically for the no-store and max-age values. If the Cache-Control header contains any value other than these two, it’s best not to cache the response.

1-9 Compression. Add support for HTTP compression, in which the browser informs the server that compressed data is acceptable. Your browser must send the Accept-Encoding header with the value gzip. If the server supports compression, its response will have a Content-Encoding header with value gzip. The body is then compressed. Add support for this case. To decompress the data, you can use the decompress method in the gzip module. GZip data is not utf8-encoded, so pass "rb" to makefile to work with raw bytes instead. Most web servers send compressed data in a Transfer-Encoding called chunked. You’ll need to add support for that, too.

https://browser.engineering/graphics.html

2-4 Scrollbar. Stop your browser from scrolling down past the last display list entry.This is not quite right in a real browser; the browser needs to account for extra whitespace at the bottom of the screen or the possibility of objects purposefully drawn offscreen. In Chapter 5, we’ll implement this correctly. At the right edge of the screen, draw a blue, rectangular scrollbar. Make sure the size and position of the scrollbar reflects what part of the full document the browser can see, as in Figure 5. Hide the scrollbar if the whole document fits onscreen.

2-5 Emoji. Add support for emoji to your browser 😀. Emoji are characters, and you can call create_text to draw them, but the results aren’t very good. Instead, head to the OpenMoji project, download the emoji for “grinning face” as a PNG file, resize it to 16 × 16 pixels, and save it to the same folder as the browser. Use Tk’s PhotoImage class to load the image and then the create_image method to draw it to the canvas. In fact, download the whole OpenMoji library (look for the “Get OpenMojis” button at the top right)—then your browser can look up whatever emoji is used in the page.

2-7 Alternate text direction. Not all languages read and lay out from left to right. Arabic, Persian, and Hebrew are good examples of right-to-left languages. Implement basic support for this with a command-line flag to your browser.Once we get to Chapter 4 you could write it in terms of the dir attribute on the <body> element. English sentences should still lay out left-to-right, but they should grow from the right side of the screen (load this example in your favorite browser to see what I mean).

https://browser.engineering/text.html
skip 3rd one since trivial

https://browser.engineering/html.html
skip 4
