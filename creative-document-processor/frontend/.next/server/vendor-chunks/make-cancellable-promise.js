"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/make-cancellable-promise";
exports.ids = ["vendor-chunks/make-cancellable-promise"];
exports.modules = {

/***/ "(ssr)/./node_modules/make-cancellable-promise/dist/esm/index.js":
/*!*****************************************************************!*\
  !*** ./node_modules/make-cancellable-promise/dist/esm/index.js ***!
  \*****************************************************************/
/***/ ((__unused_webpack___webpack_module__, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (/* binding */ makeCancellablePromise)\n/* harmony export */ });\nfunction makeCancellablePromise(promise) {\n    var isCancelled = false;\n    var wrappedPromise = new Promise(function(resolve, reject) {\n        promise.then(function(value) {\n            return !isCancelled && resolve(value);\n        }).catch(function(error) {\n            return !isCancelled && reject(error);\n        });\n    });\n    return {\n        promise: wrappedPromise,\n        cancel: function() {\n            isCancelled = true;\n        }\n    };\n}\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvbWFrZS1jYW5jZWxsYWJsZS1wcm9taXNlL2Rpc3QvZXNtL2luZGV4LmpzIiwibWFwcGluZ3MiOiI7Ozs7QUFBZSxTQUFTQSx1QkFBdUJDLE9BQU87SUFDbEQsSUFBSUMsY0FBYztJQUNsQixJQUFJQyxpQkFBaUIsSUFBSUMsUUFBUSxTQUFVQyxPQUFPLEVBQUVDLE1BQU07UUFDdERMLFFBQ0tNLElBQUksQ0FBQyxTQUFVQyxLQUFLO1lBQUksT0FBTyxDQUFDTixlQUFlRyxRQUFRRztRQUFRLEdBQy9EQyxLQUFLLENBQUMsU0FBVUMsS0FBSztZQUFJLE9BQU8sQ0FBQ1IsZUFBZUksT0FBT0k7UUFBUTtJQUN4RTtJQUNBLE9BQU87UUFDSFQsU0FBU0U7UUFDVFEsUUFBUTtZQUNKVCxjQUFjO1FBQ2xCO0lBQ0o7QUFDSiIsInNvdXJjZXMiOlsid2VicGFjazovL2NyZWF0aXZlLWRvY3VtZW50LXByb2Nlc3Nvci1mcm9udGVuZC8uL25vZGVfbW9kdWxlcy9tYWtlLWNhbmNlbGxhYmxlLXByb21pc2UvZGlzdC9lc20vaW5kZXguanM/NmI0YyJdLCJzb3VyY2VzQ29udGVudCI6WyJleHBvcnQgZGVmYXVsdCBmdW5jdGlvbiBtYWtlQ2FuY2VsbGFibGVQcm9taXNlKHByb21pc2UpIHtcbiAgICB2YXIgaXNDYW5jZWxsZWQgPSBmYWxzZTtcbiAgICB2YXIgd3JhcHBlZFByb21pc2UgPSBuZXcgUHJvbWlzZShmdW5jdGlvbiAocmVzb2x2ZSwgcmVqZWN0KSB7XG4gICAgICAgIHByb21pc2VcbiAgICAgICAgICAgIC50aGVuKGZ1bmN0aW9uICh2YWx1ZSkgeyByZXR1cm4gIWlzQ2FuY2VsbGVkICYmIHJlc29sdmUodmFsdWUpOyB9KVxuICAgICAgICAgICAgLmNhdGNoKGZ1bmN0aW9uIChlcnJvcikgeyByZXR1cm4gIWlzQ2FuY2VsbGVkICYmIHJlamVjdChlcnJvcik7IH0pO1xuICAgIH0pO1xuICAgIHJldHVybiB7XG4gICAgICAgIHByb21pc2U6IHdyYXBwZWRQcm9taXNlLFxuICAgICAgICBjYW5jZWw6IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIGlzQ2FuY2VsbGVkID0gdHJ1ZTtcbiAgICAgICAgfSxcbiAgICB9O1xufVxuIl0sIm5hbWVzIjpbIm1ha2VDYW5jZWxsYWJsZVByb21pc2UiLCJwcm9taXNlIiwiaXNDYW5jZWxsZWQiLCJ3cmFwcGVkUHJvbWlzZSIsIlByb21pc2UiLCJyZXNvbHZlIiwicmVqZWN0IiwidGhlbiIsInZhbHVlIiwiY2F0Y2giLCJlcnJvciIsImNhbmNlbCJdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/make-cancellable-promise/dist/esm/index.js\n");

/***/ })

};
;