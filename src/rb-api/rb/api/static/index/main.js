function ss(e) {
  return e && e.__esModule && Object.prototype.hasOwnProperty.call(e, "default")
    ? e.default
    : e;
}
var uc = { exports: {} },
  Zo = {},
  cc = { exports: {} },
  M = {};
/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */ var Dr = Symbol.for("react.element"),
  gp = Symbol.for("react.portal"),
  wp = Symbol.for("react.fragment"),
  Sp = Symbol.for("react.strict_mode"),
  kp = Symbol.for("react.profiler"),
  xp = Symbol.for("react.provider"),
  Cp = Symbol.for("react.context"),
  Ep = Symbol.for("react.forward_ref"),
  _p = Symbol.for("react.suspense"),
  $p = Symbol.for("react.memo"),
  Np = Symbol.for("react.lazy"),
  Ea = Symbol.iterator;
function Pp(e) {
  return e === null || typeof e != "object"
    ? null
    : ((e = (Ea && e[Ea]) || e["@@iterator"]),
      typeof e == "function" ? e : null);
}
var fc = {
    isMounted: function () {
      return !1;
    },
    enqueueForceUpdate: function () {},
    enqueueReplaceState: function () {},
    enqueueSetState: function () {},
  },
  dc = Object.assign,
  pc = {};
function Bn(e, t, n) {
  (this.props = e),
    (this.context = t),
    (this.refs = pc),
    (this.updater = n || fc);
}
Bn.prototype.isReactComponent = {};
Bn.prototype.setState = function (e, t) {
  if (typeof e != "object" && typeof e != "function" && e != null)
    throw Error(
      "setState(...): takes an object of state variables to update or a function which returns an object of state variables."
    );
  this.updater.enqueueSetState(this, e, t, "setState");
};
Bn.prototype.forceUpdate = function (e) {
  this.updater.enqueueForceUpdate(this, e, "forceUpdate");
};
function mc() {}
mc.prototype = Bn.prototype;
function as(e, t, n) {
  (this.props = e),
    (this.context = t),
    (this.refs = pc),
    (this.updater = n || fc);
}
var us = (as.prototype = new mc());
us.constructor = as;
dc(us, Bn.prototype);
us.isPureReactComponent = !0;
var _a = Array.isArray,
  hc = Object.prototype.hasOwnProperty,
  cs = { current: null },
  yc = { key: !0, ref: !0, __self: !0, __source: !0 };
function vc(e, t, n) {
  var r,
    o = {},
    i = null,
    l = null;
  if (t != null)
    for (r in (t.ref !== void 0 && (l = t.ref),
    t.key !== void 0 && (i = "" + t.key),
    t))
      hc.call(t, r) && !yc.hasOwnProperty(r) && (o[r] = t[r]);
  var s = arguments.length - 2;
  if (s === 1) o.children = n;
  else if (1 < s) {
    for (var a = Array(s), u = 0; u < s; u++) a[u] = arguments[u + 2];
    o.children = a;
  }
  if (e && e.defaultProps)
    for (r in ((s = e.defaultProps), s)) o[r] === void 0 && (o[r] = s[r]);
  return {
    $$typeof: Dr,
    type: e,
    key: i,
    ref: l,
    props: o,
    _owner: cs.current,
  };
}
function jp(e, t) {
  return {
    $$typeof: Dr,
    type: e.type,
    key: t,
    ref: e.ref,
    props: e.props,
    _owner: e._owner,
  };
}
function fs(e) {
  return typeof e == "object" && e !== null && e.$$typeof === Dr;
}
function Tp(e) {
  var t = { "=": "=0", ":": "=2" };
  return (
    "$" +
    e.replace(/[=:]/g, function (n) {
      return t[n];
    })
  );
}
var $a = /\/+/g;
function Ei(e, t) {
  return typeof e == "object" && e !== null && e.key != null
    ? Tp("" + e.key)
    : t.toString(36);
}
function ho(e, t, n, r, o) {
  var i = typeof e;
  (i === "undefined" || i === "boolean") && (e = null);
  var l = !1;
  if (e === null) l = !0;
  else
    switch (i) {
      case "string":
      case "number":
        l = !0;
        break;
      case "object":
        switch (e.$$typeof) {
          case Dr:
          case gp:
            l = !0;
        }
    }
  if (l)
    return (
      (l = e),
      (o = o(l)),
      (e = r === "" ? "." + Ei(l, 0) : r),
      _a(o)
        ? ((n = ""),
          e != null && (n = e.replace($a, "$&/") + "/"),
          ho(o, t, n, "", function (u) {
            return u;
          }))
        : o != null &&
          (fs(o) &&
            (o = jp(
              o,
              n +
                (!o.key || (l && l.key === o.key)
                  ? ""
                  : ("" + o.key).replace($a, "$&/") + "/") +
                e
            )),
          t.push(o)),
      1
    );
  if (((l = 0), (r = r === "" ? "." : r + ":"), _a(e)))
    for (var s = 0; s < e.length; s++) {
      i = e[s];
      var a = r + Ei(i, s);
      l += ho(i, t, n, a, o);
    }
  else if (((a = Pp(e)), typeof a == "function"))
    for (e = a.call(e), s = 0; !(i = e.next()).done; )
      (i = i.value), (a = r + Ei(i, s++)), (l += ho(i, t, n, a, o));
  else if (i === "object")
    throw (
      ((t = String(e)),
      Error(
        "Objects are not valid as a React child (found: " +
          (t === "[object Object]"
            ? "object with keys {" + Object.keys(e).join(", ") + "}"
            : t) +
          "). If you meant to render a collection of children, use an array instead."
      ))
    );
  return l;
}
function Qr(e, t, n) {
  if (e == null) return e;
  var r = [],
    o = 0;
  return (
    ho(e, r, "", "", function (i) {
      return t.call(n, i, o++);
    }),
    r
  );
}
function Rp(e) {
  if (e._status === -1) {
    var t = e._result;
    (t = t()),
      t.then(
        function (n) {
          (e._status === 0 || e._status === -1) &&
            ((e._status = 1), (e._result = n));
        },
        function (n) {
          (e._status === 0 || e._status === -1) &&
            ((e._status = 2), (e._result = n));
        }
      ),
      e._status === -1 && ((e._status = 0), (e._result = t));
  }
  if (e._status === 1) return e._result.default;
  throw e._result;
}
var Ne = { current: null },
  yo = { transition: null },
  zp = {
    ReactCurrentDispatcher: Ne,
    ReactCurrentBatchConfig: yo,
    ReactCurrentOwner: cs,
  };
function gc() {
  throw Error("act(...) is not supported in production builds of React.");
}
M.Children = {
  map: Qr,
  forEach: function (e, t, n) {
    Qr(
      e,
      function () {
        t.apply(this, arguments);
      },
      n
    );
  },
  count: function (e) {
    var t = 0;
    return (
      Qr(e, function () {
        t++;
      }),
      t
    );
  },
  toArray: function (e) {
    return (
      Qr(e, function (t) {
        return t;
      }) || []
    );
  },
  only: function (e) {
    if (!fs(e))
      throw Error(
        "React.Children.only expected to receive a single React element child."
      );
    return e;
  },
};
M.Component = Bn;
M.Fragment = wp;
M.Profiler = kp;
M.PureComponent = as;
M.StrictMode = Sp;
M.Suspense = _p;
M.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = zp;
M.act = gc;
M.cloneElement = function (e, t, n) {
  if (e == null)
    throw Error(
      "React.cloneElement(...): The argument must be a React element, but you passed " +
        e +
        "."
    );
  var r = dc({}, e.props),
    o = e.key,
    i = e.ref,
    l = e._owner;
  if (t != null) {
    if (
      (t.ref !== void 0 && ((i = t.ref), (l = cs.current)),
      t.key !== void 0 && (o = "" + t.key),
      e.type && e.type.defaultProps)
    )
      var s = e.type.defaultProps;
    for (a in t)
      hc.call(t, a) &&
        !yc.hasOwnProperty(a) &&
        (r[a] = t[a] === void 0 && s !== void 0 ? s[a] : t[a]);
  }
  var a = arguments.length - 2;
  if (a === 1) r.children = n;
  else if (1 < a) {
    s = Array(a);
    for (var u = 0; u < a; u++) s[u] = arguments[u + 2];
    r.children = s;
  }
  return { $$typeof: Dr, type: e.type, key: o, ref: i, props: r, _owner: l };
};
M.createContext = function (e) {
  return (
    (e = {
      $$typeof: Cp,
      _currentValue: e,
      _currentValue2: e,
      _threadCount: 0,
      Provider: null,
      Consumer: null,
      _defaultValue: null,
      _globalName: null,
    }),
    (e.Provider = { $$typeof: xp, _context: e }),
    (e.Consumer = e)
  );
};
M.createElement = vc;
M.createFactory = function (e) {
  var t = vc.bind(null, e);
  return (t.type = e), t;
};
M.createRef = function () {
  return { current: null };
};
M.forwardRef = function (e) {
  return { $$typeof: Ep, render: e };
};
M.isValidElement = fs;
M.lazy = function (e) {
  return { $$typeof: Np, _payload: { _status: -1, _result: e }, _init: Rp };
};
M.memo = function (e, t) {
  return { $$typeof: $p, type: e, compare: t === void 0 ? null : t };
};
M.startTransition = function (e) {
  var t = yo.transition;
  yo.transition = {};
  try {
    e();
  } finally {
    yo.transition = t;
  }
};
M.unstable_act = gc;
M.useCallback = function (e, t) {
  return Ne.current.useCallback(e, t);
};
M.useContext = function (e) {
  return Ne.current.useContext(e);
};
M.useDebugValue = function () {};
M.useDeferredValue = function (e) {
  return Ne.current.useDeferredValue(e);
};
M.useEffect = function (e, t) {
  return Ne.current.useEffect(e, t);
};
M.useId = function () {
  return Ne.current.useId();
};
M.useImperativeHandle = function (e, t, n) {
  return Ne.current.useImperativeHandle(e, t, n);
};
M.useInsertionEffect = function (e, t) {
  return Ne.current.useInsertionEffect(e, t);
};
M.useLayoutEffect = function (e, t) {
  return Ne.current.useLayoutEffect(e, t);
};
M.useMemo = function (e, t) {
  return Ne.current.useMemo(e, t);
};
M.useReducer = function (e, t, n) {
  return Ne.current.useReducer(e, t, n);
};
M.useRef = function (e) {
  return Ne.current.useRef(e);
};
M.useState = function (e) {
  return Ne.current.useState(e);
};
M.useSyncExternalStore = function (e, t, n) {
  return Ne.current.useSyncExternalStore(e, t, n);
};
M.useTransition = function () {
  return Ne.current.useTransition();
};
M.version = "18.3.1";
cc.exports = M;
var x = cc.exports;
const Lp = ss(x);
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */ var Ip = x,
  Op = Symbol.for("react.element"),
  Fp = Symbol.for("react.fragment"),
  Mp = Object.prototype.hasOwnProperty,
  Dp = Ip.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner,
  Vp = { key: !0, ref: !0, __self: !0, __source: !0 };
function wc(e, t, n) {
  var r,
    o = {},
    i = null,
    l = null;
  n !== void 0 && (i = "" + n),
    t.key !== void 0 && (i = "" + t.key),
    t.ref !== void 0 && (l = t.ref);
  for (r in t) Mp.call(t, r) && !Vp.hasOwnProperty(r) && (o[r] = t[r]);
  if (e && e.defaultProps)
    for (r in ((t = e.defaultProps), t)) o[r] === void 0 && (o[r] = t[r]);
  return {
    $$typeof: Op,
    type: e,
    key: i,
    ref: l,
    props: o,
    _owner: Dp.current,
  };
}
Zo.Fragment = Fp;
Zo.jsx = wc;
Zo.jsxs = wc;
uc.exports = Zo;
var k = uc.exports,
  Sc = { exports: {} },
  Ae = {},
  kc = { exports: {} },
  xc = {};
/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */ (function (e) {
  function t(T, L) {
    var z = T.length;
    T.push(L);
    e: for (; 0 < z; ) {
      var j = (z - 1) >>> 1,
        F = T[j];
      if (0 < o(F, L)) (T[j] = L), (T[z] = F), (z = j);
      else break e;
    }
  }
  function n(T) {
    return T.length === 0 ? null : T[0];
  }
  function r(T) {
    if (T.length === 0) return null;
    var L = T[0],
      z = T.pop();
    if (z !== L) {
      T[0] = z;
      e: for (var j = 0, F = T.length, B = F >>> 1; j < B; ) {
        var J = 2 * (j + 1) - 1,
          Oe = T[J],
          fe = J + 1,
          ne = T[fe];
        if (0 > o(Oe, z))
          fe < F && 0 > o(ne, Oe)
            ? ((T[j] = ne), (T[fe] = z), (j = fe))
            : ((T[j] = Oe), (T[J] = z), (j = J));
        else if (fe < F && 0 > o(ne, z)) (T[j] = ne), (T[fe] = z), (j = fe);
        else break e;
      }
    }
    return L;
  }
  function o(T, L) {
    var z = T.sortIndex - L.sortIndex;
    return z !== 0 ? z : T.id - L.id;
  }
  if (typeof performance == "object" && typeof performance.now == "function") {
    var i = performance;
    e.unstable_now = function () {
      return i.now();
    };
  } else {
    var l = Date,
      s = l.now();
    e.unstable_now = function () {
      return l.now() - s;
    };
  }
  var a = [],
    u = [],
    f = 1,
    d = null,
    h = 3,
    g = !1,
    y = !1,
    v = !1,
    C = typeof setTimeout == "function" ? setTimeout : null,
    m = typeof clearTimeout == "function" ? clearTimeout : null,
    c = typeof setImmediate < "u" ? setImmediate : null;
  typeof navigator < "u" &&
    navigator.scheduling !== void 0 &&
    navigator.scheduling.isInputPending !== void 0 &&
    navigator.scheduling.isInputPending.bind(navigator.scheduling);
  function p(T) {
    for (var L = n(u); L !== null; ) {
      if (L.callback === null) r(u);
      else if (L.startTime <= T)
        r(u), (L.sortIndex = L.expirationTime), t(a, L);
      else break;
      L = n(u);
    }
  }
  function S(T) {
    if (((v = !1), p(T), !y))
      if (n(a) !== null) (y = !0), ce(_);
      else {
        var L = n(u);
        L !== null && je(S, L.startTime - T);
      }
  }
  function _(T, L) {
    (y = !1), v && ((v = !1), m(N), (N = -1)), (g = !0);
    var z = h;
    try {
      for (
        p(L), d = n(a);
        d !== null && (!(d.expirationTime > L) || (T && !b()));

      ) {
        var j = d.callback;
        if (typeof j == "function") {
          (d.callback = null), (h = d.priorityLevel);
          var F = j(d.expirationTime <= L);
          (L = e.unstable_now()),
            typeof F == "function" ? (d.callback = F) : d === n(a) && r(a),
            p(L);
        } else r(a);
        d = n(a);
      }
      if (d !== null) var B = !0;
      else {
        var J = n(u);
        J !== null && je(S, J.startTime - L), (B = !1);
      }
      return B;
    } finally {
      (d = null), (h = z), (g = !1);
    }
  }
  var w = !1,
    E = null,
    N = -1,
    I = 5,
    O = -1;
  function b() {
    return !(e.unstable_now() - O < I);
  }
  function ie() {
    if (E !== null) {
      var T = e.unstable_now();
      O = T;
      var L = !0;
      try {
        L = E(!0, T);
      } finally {
        L ? W() : ((w = !1), (E = null));
      }
    } else w = !1;
  }
  var W;
  if (typeof c == "function")
    W = function () {
      c(ie);
    };
  else if (typeof MessageChannel < "u") {
    var le = new MessageChannel(),
      Xe = le.port2;
    (le.port1.onmessage = ie),
      (W = function () {
        Xe.postMessage(null);
      });
  } else
    W = function () {
      C(ie, 0);
    };
  function ce(T) {
    (E = T), w || ((w = !0), W());
  }
  function je(T, L) {
    N = C(function () {
      T(e.unstable_now());
    }, L);
  }
  (e.unstable_IdlePriority = 5),
    (e.unstable_ImmediatePriority = 1),
    (e.unstable_LowPriority = 4),
    (e.unstable_NormalPriority = 3),
    (e.unstable_Profiling = null),
    (e.unstable_UserBlockingPriority = 2),
    (e.unstable_cancelCallback = function (T) {
      T.callback = null;
    }),
    (e.unstable_continueExecution = function () {
      y || g || ((y = !0), ce(_));
    }),
    (e.unstable_forceFrameRate = function (T) {
      0 > T || 125 < T
        ? console.error(
            "forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported"
          )
        : (I = 0 < T ? Math.floor(1e3 / T) : 5);
    }),
    (e.unstable_getCurrentPriorityLevel = function () {
      return h;
    }),
    (e.unstable_getFirstCallbackNode = function () {
      return n(a);
    }),
    (e.unstable_next = function (T) {
      switch (h) {
        case 1:
        case 2:
        case 3:
          var L = 3;
          break;
        default:
          L = h;
      }
      var z = h;
      h = L;
      try {
        return T();
      } finally {
        h = z;
      }
    }),
    (e.unstable_pauseExecution = function () {}),
    (e.unstable_requestPaint = function () {}),
    (e.unstable_runWithPriority = function (T, L) {
      switch (T) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
          break;
        default:
          T = 3;
      }
      var z = h;
      h = T;
      try {
        return L();
      } finally {
        h = z;
      }
    }),
    (e.unstable_scheduleCallback = function (T, L, z) {
      var j = e.unstable_now();
      switch (
        (typeof z == "object" && z !== null
          ? ((z = z.delay), (z = typeof z == "number" && 0 < z ? j + z : j))
          : (z = j),
        T)
      ) {
        case 1:
          var F = -1;
          break;
        case 2:
          F = 250;
          break;
        case 5:
          F = 1073741823;
          break;
        case 4:
          F = 1e4;
          break;
        default:
          F = 5e3;
      }
      return (
        (F = z + F),
        (T = {
          id: f++,
          callback: L,
          priorityLevel: T,
          startTime: z,
          expirationTime: F,
          sortIndex: -1,
        }),
        z > j
          ? ((T.sortIndex = z),
            t(u, T),
            n(a) === null &&
              T === n(u) &&
              (v ? (m(N), (N = -1)) : (v = !0), je(S, z - j)))
          : ((T.sortIndex = F), t(a, T), y || g || ((y = !0), ce(_))),
        T
      );
    }),
    (e.unstable_shouldYield = b),
    (e.unstable_wrapCallback = function (T) {
      var L = h;
      return function () {
        var z = h;
        h = L;
        try {
          return T.apply(this, arguments);
        } finally {
          h = z;
        }
      };
    });
})(xc);
kc.exports = xc;
var Ap = kc.exports;
/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */ var Bp = x,
  Ve = Ap;
function P(e) {
  for (
    var t = "https://reactjs.org/docs/error-decoder.html?invariant=" + e, n = 1;
    n < arguments.length;
    n++
  )
    t += "&args[]=" + encodeURIComponent(arguments[n]);
  return (
    "Minified React error #" +
    e +
    "; visit " +
    t +
    " for the full message or use the non-minified dev environment for full errors and additional helpful warnings."
  );
}
var Cc = new Set(),
  gr = {};
function ln(e, t) {
  In(e, t), In(e + "Capture", t);
}
function In(e, t) {
  for (gr[e] = t, e = 0; e < t.length; e++) Cc.add(t[e]);
}
var gt = !(
    typeof window > "u" ||
    typeof window.document > "u" ||
    typeof window.document.createElement > "u"
  ),
  ol = Object.prototype.hasOwnProperty,
  Wp =
    /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/,
  Na = {},
  Pa = {};
function Up(e) {
  return ol.call(Pa, e)
    ? !0
    : ol.call(Na, e)
    ? !1
    : Wp.test(e)
    ? (Pa[e] = !0)
    : ((Na[e] = !0), !1);
}
function Hp(e, t, n, r) {
  if (n !== null && n.type === 0) return !1;
  switch (typeof t) {
    case "function":
    case "symbol":
      return !0;
    case "boolean":
      return r
        ? !1
        : n !== null
        ? !n.acceptsBooleans
        : ((e = e.toLowerCase().slice(0, 5)), e !== "data-" && e !== "aria-");
    default:
      return !1;
  }
}
function bp(e, t, n, r) {
  if (t === null || typeof t > "u" || Hp(e, t, n, r)) return !0;
  if (r) return !1;
  if (n !== null)
    switch (n.type) {
      case 3:
        return !t;
      case 4:
        return t === !1;
      case 5:
        return isNaN(t);
      case 6:
        return isNaN(t) || 1 > t;
    }
  return !1;
}
function Pe(e, t, n, r, o, i, l) {
  (this.acceptsBooleans = t === 2 || t === 3 || t === 4),
    (this.attributeName = r),
    (this.attributeNamespace = o),
    (this.mustUseProperty = n),
    (this.propertyName = e),
    (this.type = t),
    (this.sanitizeURL = i),
    (this.removeEmptyString = l);
}
var he = {};
"children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style"
  .split(" ")
  .forEach(function (e) {
    he[e] = new Pe(e, 0, !1, e, null, !1, !1);
  });
[
  ["acceptCharset", "accept-charset"],
  ["className", "class"],
  ["htmlFor", "for"],
  ["httpEquiv", "http-equiv"],
].forEach(function (e) {
  var t = e[0];
  he[t] = new Pe(t, 1, !1, e[1], null, !1, !1);
});
["contentEditable", "draggable", "spellCheck", "value"].forEach(function (e) {
  he[e] = new Pe(e, 2, !1, e.toLowerCase(), null, !1, !1);
});
[
  "autoReverse",
  "externalResourcesRequired",
  "focusable",
  "preserveAlpha",
].forEach(function (e) {
  he[e] = new Pe(e, 2, !1, e, null, !1, !1);
});
"allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope"
  .split(" ")
  .forEach(function (e) {
    he[e] = new Pe(e, 3, !1, e.toLowerCase(), null, !1, !1);
  });
["checked", "multiple", "muted", "selected"].forEach(function (e) {
  he[e] = new Pe(e, 3, !0, e, null, !1, !1);
});
["capture", "download"].forEach(function (e) {
  he[e] = new Pe(e, 4, !1, e, null, !1, !1);
});
["cols", "rows", "size", "span"].forEach(function (e) {
  he[e] = new Pe(e, 6, !1, e, null, !1, !1);
});
["rowSpan", "start"].forEach(function (e) {
  he[e] = new Pe(e, 5, !1, e.toLowerCase(), null, !1, !1);
});
var ds = /[\-:]([a-z])/g;
function ps(e) {
  return e[1].toUpperCase();
}
"accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height"
  .split(" ")
  .forEach(function (e) {
    var t = e.replace(ds, ps);
    he[t] = new Pe(t, 1, !1, e, null, !1, !1);
  });
"xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type"
  .split(" ")
  .forEach(function (e) {
    var t = e.replace(ds, ps);
    he[t] = new Pe(t, 1, !1, e, "http://www.w3.org/1999/xlink", !1, !1);
  });
["xml:base", "xml:lang", "xml:space"].forEach(function (e) {
  var t = e.replace(ds, ps);
  he[t] = new Pe(t, 1, !1, e, "http://www.w3.org/XML/1998/namespace", !1, !1);
});
["tabIndex", "crossOrigin"].forEach(function (e) {
  he[e] = new Pe(e, 1, !1, e.toLowerCase(), null, !1, !1);
});
he.xlinkHref = new Pe(
  "xlinkHref",
  1,
  !1,
  "xlink:href",
  "http://www.w3.org/1999/xlink",
  !0,
  !1
);
["src", "href", "action", "formAction"].forEach(function (e) {
  he[e] = new Pe(e, 1, !1, e.toLowerCase(), null, !0, !0);
});
function ms(e, t, n, r) {
  var o = he.hasOwnProperty(t) ? he[t] : null;
  (o !== null
    ? o.type !== 0
    : r ||
      !(2 < t.length) ||
      (t[0] !== "o" && t[0] !== "O") ||
      (t[1] !== "n" && t[1] !== "N")) &&
    (bp(t, n, o, r) && (n = null),
    r || o === null
      ? Up(t) && (n === null ? e.removeAttribute(t) : e.setAttribute(t, "" + n))
      : o.mustUseProperty
      ? (e[o.propertyName] = n === null ? (o.type === 3 ? !1 : "") : n)
      : ((t = o.attributeName),
        (r = o.attributeNamespace),
        n === null
          ? e.removeAttribute(t)
          : ((o = o.type),
            (n = o === 3 || (o === 4 && n === !0) ? "" : "" + n),
            r ? e.setAttributeNS(r, t, n) : e.setAttribute(t, n))));
}
var xt = Bp.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED,
  Gr = Symbol.for("react.element"),
  mn = Symbol.for("react.portal"),
  hn = Symbol.for("react.fragment"),
  hs = Symbol.for("react.strict_mode"),
  il = Symbol.for("react.profiler"),
  Ec = Symbol.for("react.provider"),
  _c = Symbol.for("react.context"),
  ys = Symbol.for("react.forward_ref"),
  ll = Symbol.for("react.suspense"),
  sl = Symbol.for("react.suspense_list"),
  vs = Symbol.for("react.memo"),
  Nt = Symbol.for("react.lazy"),
  $c = Symbol.for("react.offscreen"),
  ja = Symbol.iterator;
function Qn(e) {
  return e === null || typeof e != "object"
    ? null
    : ((e = (ja && e[ja]) || e["@@iterator"]),
      typeof e == "function" ? e : null);
}
var Z = Object.assign,
  _i;
function or(e) {
  if (_i === void 0)
    try {
      throw Error();
    } catch (n) {
      var t = n.stack.trim().match(/\n( *(at )?)/);
      _i = (t && t[1]) || "";
    }
  return (
    `
` +
    _i +
    e
  );
}
var $i = !1;
function Ni(e, t) {
  if (!e || $i) return "";
  $i = !0;
  var n = Error.prepareStackTrace;
  Error.prepareStackTrace = void 0;
  try {
    if (t)
      if (
        ((t = function () {
          throw Error();
        }),
        Object.defineProperty(t.prototype, "props", {
          set: function () {
            throw Error();
          },
        }),
        typeof Reflect == "object" && Reflect.construct)
      ) {
        try {
          Reflect.construct(t, []);
        } catch (u) {
          var r = u;
        }
        Reflect.construct(e, [], t);
      } else {
        try {
          t.call();
        } catch (u) {
          r = u;
        }
        e.call(t.prototype);
      }
    else {
      try {
        throw Error();
      } catch (u) {
        r = u;
      }
      e();
    }
  } catch (u) {
    if (u && r && typeof u.stack == "string") {
      for (
        var o = u.stack.split(`
`),
          i = r.stack.split(`
`),
          l = o.length - 1,
          s = i.length - 1;
        1 <= l && 0 <= s && o[l] !== i[s];

      )
        s--;
      for (; 1 <= l && 0 <= s; l--, s--)
        if (o[l] !== i[s]) {
          if (l !== 1 || s !== 1)
            do
              if ((l--, s--, 0 > s || o[l] !== i[s])) {
                var a =
                  `
` + o[l].replace(" at new ", " at ");
                return (
                  e.displayName &&
                    a.includes("<anonymous>") &&
                    (a = a.replace("<anonymous>", e.displayName)),
                  a
                );
              }
            while (1 <= l && 0 <= s);
          break;
        }
    }
  } finally {
    ($i = !1), (Error.prepareStackTrace = n);
  }
  return (e = e ? e.displayName || e.name : "") ? or(e) : "";
}
function Qp(e) {
  switch (e.tag) {
    case 5:
      return or(e.type);
    case 16:
      return or("Lazy");
    case 13:
      return or("Suspense");
    case 19:
      return or("SuspenseList");
    case 0:
    case 2:
    case 15:
      return (e = Ni(e.type, !1)), e;
    case 11:
      return (e = Ni(e.type.render, !1)), e;
    case 1:
      return (e = Ni(e.type, !0)), e;
    default:
      return "";
  }
}
function al(e) {
  if (e == null) return null;
  if (typeof e == "function") return e.displayName || e.name || null;
  if (typeof e == "string") return e;
  switch (e) {
    case hn:
      return "Fragment";
    case mn:
      return "Portal";
    case il:
      return "Profiler";
    case hs:
      return "StrictMode";
    case ll:
      return "Suspense";
    case sl:
      return "SuspenseList";
  }
  if (typeof e == "object")
    switch (e.$$typeof) {
      case _c:
        return (e.displayName || "Context") + ".Consumer";
      case Ec:
        return (e._context.displayName || "Context") + ".Provider";
      case ys:
        var t = e.render;
        return (
          (e = e.displayName),
          e ||
            ((e = t.displayName || t.name || ""),
            (e = e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef")),
          e
        );
      case vs:
        return (
          (t = e.displayName || null), t !== null ? t : al(e.type) || "Memo"
        );
      case Nt:
        (t = e._payload), (e = e._init);
        try {
          return al(e(t));
        } catch {}
    }
  return null;
}
function Gp(e) {
  var t = e.type;
  switch (e.tag) {
    case 24:
      return "Cache";
    case 9:
      return (t.displayName || "Context") + ".Consumer";
    case 10:
      return (t._context.displayName || "Context") + ".Provider";
    case 18:
      return "DehydratedFragment";
    case 11:
      return (
        (e = t.render),
        (e = e.displayName || e.name || ""),
        t.displayName || (e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef")
      );
    case 7:
      return "Fragment";
    case 5:
      return t;
    case 4:
      return "Portal";
    case 3:
      return "Root";
    case 6:
      return "Text";
    case 16:
      return al(t);
    case 8:
      return t === hs ? "StrictMode" : "Mode";
    case 22:
      return "Offscreen";
    case 12:
      return "Profiler";
    case 21:
      return "Scope";
    case 13:
      return "Suspense";
    case 19:
      return "SuspenseList";
    case 25:
      return "TracingMarker";
    case 1:
    case 0:
    case 17:
    case 2:
    case 14:
    case 15:
      if (typeof t == "function") return t.displayName || t.name || null;
      if (typeof t == "string") return t;
  }
  return null;
}
function Bt(e) {
  switch (typeof e) {
    case "boolean":
    case "number":
    case "string":
    case "undefined":
      return e;
    case "object":
      return e;
    default:
      return "";
  }
}
function Nc(e) {
  var t = e.type;
  return (
    (e = e.nodeName) &&
    e.toLowerCase() === "input" &&
    (t === "checkbox" || t === "radio")
  );
}
function Yp(e) {
  var t = Nc(e) ? "checked" : "value",
    n = Object.getOwnPropertyDescriptor(e.constructor.prototype, t),
    r = "" + e[t];
  if (
    !e.hasOwnProperty(t) &&
    typeof n < "u" &&
    typeof n.get == "function" &&
    typeof n.set == "function"
  ) {
    var o = n.get,
      i = n.set;
    return (
      Object.defineProperty(e, t, {
        configurable: !0,
        get: function () {
          return o.call(this);
        },
        set: function (l) {
          (r = "" + l), i.call(this, l);
        },
      }),
      Object.defineProperty(e, t, { enumerable: n.enumerable }),
      {
        getValue: function () {
          return r;
        },
        setValue: function (l) {
          r = "" + l;
        },
        stopTracking: function () {
          (e._valueTracker = null), delete e[t];
        },
      }
    );
  }
}
function Yr(e) {
  e._valueTracker || (e._valueTracker = Yp(e));
}
function Pc(e) {
  if (!e) return !1;
  var t = e._valueTracker;
  if (!t) return !0;
  var n = t.getValue(),
    r = "";
  return (
    e && (r = Nc(e) ? (e.checked ? "true" : "false") : e.value),
    (e = r),
    e !== n ? (t.setValue(e), !0) : !1
  );
}
function No(e) {
  if (((e = e || (typeof document < "u" ? document : void 0)), typeof e > "u"))
    return null;
  try {
    return e.activeElement || e.body;
  } catch {
    return e.body;
  }
}
function ul(e, t) {
  var n = t.checked;
  return Z({}, t, {
    defaultChecked: void 0,
    defaultValue: void 0,
    value: void 0,
    checked: n ?? e._wrapperState.initialChecked,
  });
}
function Ta(e, t) {
  var n = t.defaultValue == null ? "" : t.defaultValue,
    r = t.checked != null ? t.checked : t.defaultChecked;
  (n = Bt(t.value != null ? t.value : n)),
    (e._wrapperState = {
      initialChecked: r,
      initialValue: n,
      controlled:
        t.type === "checkbox" || t.type === "radio"
          ? t.checked != null
          : t.value != null,
    });
}
function jc(e, t) {
  (t = t.checked), t != null && ms(e, "checked", t, !1);
}
function cl(e, t) {
  jc(e, t);
  var n = Bt(t.value),
    r = t.type;
  if (n != null)
    r === "number"
      ? ((n === 0 && e.value === "") || e.value != n) && (e.value = "" + n)
      : e.value !== "" + n && (e.value = "" + n);
  else if (r === "submit" || r === "reset") {
    e.removeAttribute("value");
    return;
  }
  t.hasOwnProperty("value")
    ? fl(e, t.type, n)
    : t.hasOwnProperty("defaultValue") && fl(e, t.type, Bt(t.defaultValue)),
    t.checked == null &&
      t.defaultChecked != null &&
      (e.defaultChecked = !!t.defaultChecked);
}
function Ra(e, t, n) {
  if (t.hasOwnProperty("value") || t.hasOwnProperty("defaultValue")) {
    var r = t.type;
    if (
      !(
        (r !== "submit" && r !== "reset") ||
        (t.value !== void 0 && t.value !== null)
      )
    )
      return;
    (t = "" + e._wrapperState.initialValue),
      n || t === e.value || (e.value = t),
      (e.defaultValue = t);
  }
  (n = e.name),
    n !== "" && (e.name = ""),
    (e.defaultChecked = !!e._wrapperState.initialChecked),
    n !== "" && (e.name = n);
}
function fl(e, t, n) {
  (t !== "number" || No(e.ownerDocument) !== e) &&
    (n == null
      ? (e.defaultValue = "" + e._wrapperState.initialValue)
      : e.defaultValue !== "" + n && (e.defaultValue = "" + n));
}
var ir = Array.isArray;
function Nn(e, t, n, r) {
  if (((e = e.options), t)) {
    t = {};
    for (var o = 0; o < n.length; o++) t["$" + n[o]] = !0;
    for (n = 0; n < e.length; n++)
      (o = t.hasOwnProperty("$" + e[n].value)),
        e[n].selected !== o && (e[n].selected = o),
        o && r && (e[n].defaultSelected = !0);
  } else {
    for (n = "" + Bt(n), t = null, o = 0; o < e.length; o++) {
      if (e[o].value === n) {
        (e[o].selected = !0), r && (e[o].defaultSelected = !0);
        return;
      }
      t !== null || e[o].disabled || (t = e[o]);
    }
    t !== null && (t.selected = !0);
  }
}
function dl(e, t) {
  if (t.dangerouslySetInnerHTML != null) throw Error(P(91));
  return Z({}, t, {
    value: void 0,
    defaultValue: void 0,
    children: "" + e._wrapperState.initialValue,
  });
}
function za(e, t) {
  var n = t.value;
  if (n == null) {
    if (((n = t.children), (t = t.defaultValue), n != null)) {
      if (t != null) throw Error(P(92));
      if (ir(n)) {
        if (1 < n.length) throw Error(P(93));
        n = n[0];
      }
      t = n;
    }
    t == null && (t = ""), (n = t);
  }
  e._wrapperState = { initialValue: Bt(n) };
}
function Tc(e, t) {
  var n = Bt(t.value),
    r = Bt(t.defaultValue);
  n != null &&
    ((n = "" + n),
    n !== e.value && (e.value = n),
    t.defaultValue == null && e.defaultValue !== n && (e.defaultValue = n)),
    r != null && (e.defaultValue = "" + r);
}
function La(e) {
  var t = e.textContent;
  t === e._wrapperState.initialValue && t !== "" && t !== null && (e.value = t);
}
function Rc(e) {
  switch (e) {
    case "svg":
      return "http://www.w3.org/2000/svg";
    case "math":
      return "http://www.w3.org/1998/Math/MathML";
    default:
      return "http://www.w3.org/1999/xhtml";
  }
}
function pl(e, t) {
  return e == null || e === "http://www.w3.org/1999/xhtml"
    ? Rc(t)
    : e === "http://www.w3.org/2000/svg" && t === "foreignObject"
    ? "http://www.w3.org/1999/xhtml"
    : e;
}
var Kr,
  zc = (function (e) {
    return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction
      ? function (t, n, r, o) {
          MSApp.execUnsafeLocalFunction(function () {
            return e(t, n, r, o);
          });
        }
      : e;
  })(function (e, t) {
    if (e.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in e)
      e.innerHTML = t;
    else {
      for (
        Kr = Kr || document.createElement("div"),
          Kr.innerHTML = "<svg>" + t.valueOf().toString() + "</svg>",
          t = Kr.firstChild;
        e.firstChild;

      )
        e.removeChild(e.firstChild);
      for (; t.firstChild; ) e.appendChild(t.firstChild);
    }
  });
function wr(e, t) {
  if (t) {
    var n = e.firstChild;
    if (n && n === e.lastChild && n.nodeType === 3) {
      n.nodeValue = t;
      return;
    }
  }
  e.textContent = t;
}
var ur = {
    animationIterationCount: !0,
    aspectRatio: !0,
    borderImageOutset: !0,
    borderImageSlice: !0,
    borderImageWidth: !0,
    boxFlex: !0,
    boxFlexGroup: !0,
    boxOrdinalGroup: !0,
    columnCount: !0,
    columns: !0,
    flex: !0,
    flexGrow: !0,
    flexPositive: !0,
    flexShrink: !0,
    flexNegative: !0,
    flexOrder: !0,
    gridArea: !0,
    gridRow: !0,
    gridRowEnd: !0,
    gridRowSpan: !0,
    gridRowStart: !0,
    gridColumn: !0,
    gridColumnEnd: !0,
    gridColumnSpan: !0,
    gridColumnStart: !0,
    fontWeight: !0,
    lineClamp: !0,
    lineHeight: !0,
    opacity: !0,
    order: !0,
    orphans: !0,
    tabSize: !0,
    widows: !0,
    zIndex: !0,
    zoom: !0,
    fillOpacity: !0,
    floodOpacity: !0,
    stopOpacity: !0,
    strokeDasharray: !0,
    strokeDashoffset: !0,
    strokeMiterlimit: !0,
    strokeOpacity: !0,
    strokeWidth: !0,
  },
  Kp = ["Webkit", "ms", "Moz", "O"];
Object.keys(ur).forEach(function (e) {
  Kp.forEach(function (t) {
    (t = t + e.charAt(0).toUpperCase() + e.substring(1)), (ur[t] = ur[e]);
  });
});
function Lc(e, t, n) {
  return t == null || typeof t == "boolean" || t === ""
    ? ""
    : n || typeof t != "number" || t === 0 || (ur.hasOwnProperty(e) && ur[e])
    ? ("" + t).trim()
    : t + "px";
}
function Ic(e, t) {
  e = e.style;
  for (var n in t)
    if (t.hasOwnProperty(n)) {
      var r = n.indexOf("--") === 0,
        o = Lc(n, t[n], r);
      n === "float" && (n = "cssFloat"), r ? e.setProperty(n, o) : (e[n] = o);
    }
}
var Xp = Z(
  { menuitem: !0 },
  {
    area: !0,
    base: !0,
    br: !0,
    col: !0,
    embed: !0,
    hr: !0,
    img: !0,
    input: !0,
    keygen: !0,
    link: !0,
    meta: !0,
    param: !0,
    source: !0,
    track: !0,
    wbr: !0,
  }
);
function ml(e, t) {
  if (t) {
    if (Xp[e] && (t.children != null || t.dangerouslySetInnerHTML != null))
      throw Error(P(137, e));
    if (t.dangerouslySetInnerHTML != null) {
      if (t.children != null) throw Error(P(60));
      if (
        typeof t.dangerouslySetInnerHTML != "object" ||
        !("__html" in t.dangerouslySetInnerHTML)
      )
        throw Error(P(61));
    }
    if (t.style != null && typeof t.style != "object") throw Error(P(62));
  }
}
function hl(e, t) {
  if (e.indexOf("-") === -1) return typeof t.is == "string";
  switch (e) {
    case "annotation-xml":
    case "color-profile":
    case "font-face":
    case "font-face-src":
    case "font-face-uri":
    case "font-face-format":
    case "font-face-name":
    case "missing-glyph":
      return !1;
    default:
      return !0;
  }
}
var yl = null;
function gs(e) {
  return (
    (e = e.target || e.srcElement || window),
    e.correspondingUseElement && (e = e.correspondingUseElement),
    e.nodeType === 3 ? e.parentNode : e
  );
}
var vl = null,
  Pn = null,
  jn = null;
function Ia(e) {
  if ((e = Br(e))) {
    if (typeof vl != "function") throw Error(P(280));
    var t = e.stateNode;
    t && ((t = ni(t)), vl(e.stateNode, e.type, t));
  }
}
function Oc(e) {
  Pn ? (jn ? jn.push(e) : (jn = [e])) : (Pn = e);
}
function Fc() {
  if (Pn) {
    var e = Pn,
      t = jn;
    if (((jn = Pn = null), Ia(e), t)) for (e = 0; e < t.length; e++) Ia(t[e]);
  }
}
function Mc(e, t) {
  return e(t);
}
function Dc() {}
var Pi = !1;
function Vc(e, t, n) {
  if (Pi) return e(t, n);
  Pi = !0;
  try {
    return Mc(e, t, n);
  } finally {
    (Pi = !1), (Pn !== null || jn !== null) && (Dc(), Fc());
  }
}
function Sr(e, t) {
  var n = e.stateNode;
  if (n === null) return null;
  var r = ni(n);
  if (r === null) return null;
  n = r[t];
  e: switch (t) {
    case "onClick":
    case "onClickCapture":
    case "onDoubleClick":
    case "onDoubleClickCapture":
    case "onMouseDown":
    case "onMouseDownCapture":
    case "onMouseMove":
    case "onMouseMoveCapture":
    case "onMouseUp":
    case "onMouseUpCapture":
    case "onMouseEnter":
      (r = !r.disabled) ||
        ((e = e.type),
        (r = !(
          e === "button" ||
          e === "input" ||
          e === "select" ||
          e === "textarea"
        ))),
        (e = !r);
      break e;
    default:
      e = !1;
  }
  if (e) return null;
  if (n && typeof n != "function") throw Error(P(231, t, typeof n));
  return n;
}
var gl = !1;
if (gt)
  try {
    var Gn = {};
    Object.defineProperty(Gn, "passive", {
      get: function () {
        gl = !0;
      },
    }),
      window.addEventListener("test", Gn, Gn),
      window.removeEventListener("test", Gn, Gn);
  } catch {
    gl = !1;
  }
function Zp(e, t, n, r, o, i, l, s, a) {
  var u = Array.prototype.slice.call(arguments, 3);
  try {
    t.apply(n, u);
  } catch (f) {
    this.onError(f);
  }
}
var cr = !1,
  Po = null,
  jo = !1,
  wl = null,
  Jp = {
    onError: function (e) {
      (cr = !0), (Po = e);
    },
  };
function qp(e, t, n, r, o, i, l, s, a) {
  (cr = !1), (Po = null), Zp.apply(Jp, arguments);
}
function em(e, t, n, r, o, i, l, s, a) {
  if ((qp.apply(this, arguments), cr)) {
    if (cr) {
      var u = Po;
      (cr = !1), (Po = null);
    } else throw Error(P(198));
    jo || ((jo = !0), (wl = u));
  }
}
function sn(e) {
  var t = e,
    n = e;
  if (e.alternate) for (; t.return; ) t = t.return;
  else {
    e = t;
    do (t = e), t.flags & 4098 && (n = t.return), (e = t.return);
    while (e);
  }
  return t.tag === 3 ? n : null;
}
function Ac(e) {
  if (e.tag === 13) {
    var t = e.memoizedState;
    if (
      (t === null && ((e = e.alternate), e !== null && (t = e.memoizedState)),
      t !== null)
    )
      return t.dehydrated;
  }
  return null;
}
function Oa(e) {
  if (sn(e) !== e) throw Error(P(188));
}
function tm(e) {
  var t = e.alternate;
  if (!t) {
    if (((t = sn(e)), t === null)) throw Error(P(188));
    return t !== e ? null : e;
  }
  for (var n = e, r = t; ; ) {
    var o = n.return;
    if (o === null) break;
    var i = o.alternate;
    if (i === null) {
      if (((r = o.return), r !== null)) {
        n = r;
        continue;
      }
      break;
    }
    if (o.child === i.child) {
      for (i = o.child; i; ) {
        if (i === n) return Oa(o), e;
        if (i === r) return Oa(o), t;
        i = i.sibling;
      }
      throw Error(P(188));
    }
    if (n.return !== r.return) (n = o), (r = i);
    else {
      for (var l = !1, s = o.child; s; ) {
        if (s === n) {
          (l = !0), (n = o), (r = i);
          break;
        }
        if (s === r) {
          (l = !0), (r = o), (n = i);
          break;
        }
        s = s.sibling;
      }
      if (!l) {
        for (s = i.child; s; ) {
          if (s === n) {
            (l = !0), (n = i), (r = o);
            break;
          }
          if (s === r) {
            (l = !0), (r = i), (n = o);
            break;
          }
          s = s.sibling;
        }
        if (!l) throw Error(P(189));
      }
    }
    if (n.alternate !== r) throw Error(P(190));
  }
  if (n.tag !== 3) throw Error(P(188));
  return n.stateNode.current === n ? e : t;
}
function Bc(e) {
  return (e = tm(e)), e !== null ? Wc(e) : null;
}
function Wc(e) {
  if (e.tag === 5 || e.tag === 6) return e;
  for (e = e.child; e !== null; ) {
    var t = Wc(e);
    if (t !== null) return t;
    e = e.sibling;
  }
  return null;
}
var Uc = Ve.unstable_scheduleCallback,
  Fa = Ve.unstable_cancelCallback,
  nm = Ve.unstable_shouldYield,
  rm = Ve.unstable_requestPaint,
  ee = Ve.unstable_now,
  om = Ve.unstable_getCurrentPriorityLevel,
  ws = Ve.unstable_ImmediatePriority,
  Hc = Ve.unstable_UserBlockingPriority,
  To = Ve.unstable_NormalPriority,
  im = Ve.unstable_LowPriority,
  bc = Ve.unstable_IdlePriority,
  Jo = null,
  ct = null;
function lm(e) {
  if (ct && typeof ct.onCommitFiberRoot == "function")
    try {
      ct.onCommitFiberRoot(Jo, e, void 0, (e.current.flags & 128) === 128);
    } catch {}
}
var rt = Math.clz32 ? Math.clz32 : um,
  sm = Math.log,
  am = Math.LN2;
function um(e) {
  return (e >>>= 0), e === 0 ? 32 : (31 - ((sm(e) / am) | 0)) | 0;
}
var Xr = 64,
  Zr = 4194304;
function lr(e) {
  switch (e & -e) {
    case 1:
      return 1;
    case 2:
      return 2;
    case 4:
      return 4;
    case 8:
      return 8;
    case 16:
      return 16;
    case 32:
      return 32;
    case 64:
    case 128:
    case 256:
    case 512:
    case 1024:
    case 2048:
    case 4096:
    case 8192:
    case 16384:
    case 32768:
    case 65536:
    case 131072:
    case 262144:
    case 524288:
    case 1048576:
    case 2097152:
      return e & 4194240;
    case 4194304:
    case 8388608:
    case 16777216:
    case 33554432:
    case 67108864:
      return e & 130023424;
    case 134217728:
      return 134217728;
    case 268435456:
      return 268435456;
    case 536870912:
      return 536870912;
    case 1073741824:
      return 1073741824;
    default:
      return e;
  }
}
function Ro(e, t) {
  var n = e.pendingLanes;
  if (n === 0) return 0;
  var r = 0,
    o = e.suspendedLanes,
    i = e.pingedLanes,
    l = n & 268435455;
  if (l !== 0) {
    var s = l & ~o;
    s !== 0 ? (r = lr(s)) : ((i &= l), i !== 0 && (r = lr(i)));
  } else (l = n & ~o), l !== 0 ? (r = lr(l)) : i !== 0 && (r = lr(i));
  if (r === 0) return 0;
  if (
    t !== 0 &&
    t !== r &&
    !(t & o) &&
    ((o = r & -r), (i = t & -t), o >= i || (o === 16 && (i & 4194240) !== 0))
  )
    return t;
  if ((r & 4 && (r |= n & 16), (t = e.entangledLanes), t !== 0))
    for (e = e.entanglements, t &= r; 0 < t; )
      (n = 31 - rt(t)), (o = 1 << n), (r |= e[n]), (t &= ~o);
  return r;
}
function cm(e, t) {
  switch (e) {
    case 1:
    case 2:
    case 4:
      return t + 250;
    case 8:
    case 16:
    case 32:
    case 64:
    case 128:
    case 256:
    case 512:
    case 1024:
    case 2048:
    case 4096:
    case 8192:
    case 16384:
    case 32768:
    case 65536:
    case 131072:
    case 262144:
    case 524288:
    case 1048576:
    case 2097152:
      return t + 5e3;
    case 4194304:
    case 8388608:
    case 16777216:
    case 33554432:
    case 67108864:
      return -1;
    case 134217728:
    case 268435456:
    case 536870912:
    case 1073741824:
      return -1;
    default:
      return -1;
  }
}
function fm(e, t) {
  for (
    var n = e.suspendedLanes,
      r = e.pingedLanes,
      o = e.expirationTimes,
      i = e.pendingLanes;
    0 < i;

  ) {
    var l = 31 - rt(i),
      s = 1 << l,
      a = o[l];
    a === -1
      ? (!(s & n) || s & r) && (o[l] = cm(s, t))
      : a <= t && (e.expiredLanes |= s),
      (i &= ~s);
  }
}
function Sl(e) {
  return (
    (e = e.pendingLanes & -1073741825),
    e !== 0 ? e : e & 1073741824 ? 1073741824 : 0
  );
}
function Qc() {
  var e = Xr;
  return (Xr <<= 1), !(Xr & 4194240) && (Xr = 64), e;
}
function ji(e) {
  for (var t = [], n = 0; 31 > n; n++) t.push(e);
  return t;
}
function Vr(e, t, n) {
  (e.pendingLanes |= t),
    t !== 536870912 && ((e.suspendedLanes = 0), (e.pingedLanes = 0)),
    (e = e.eventTimes),
    (t = 31 - rt(t)),
    (e[t] = n);
}
function dm(e, t) {
  var n = e.pendingLanes & ~t;
  (e.pendingLanes = t),
    (e.suspendedLanes = 0),
    (e.pingedLanes = 0),
    (e.expiredLanes &= t),
    (e.mutableReadLanes &= t),
    (e.entangledLanes &= t),
    (t = e.entanglements);
  var r = e.eventTimes;
  for (e = e.expirationTimes; 0 < n; ) {
    var o = 31 - rt(n),
      i = 1 << o;
    (t[o] = 0), (r[o] = -1), (e[o] = -1), (n &= ~i);
  }
}
function Ss(e, t) {
  var n = (e.entangledLanes |= t);
  for (e = e.entanglements; n; ) {
    var r = 31 - rt(n),
      o = 1 << r;
    (o & t) | (e[r] & t) && (e[r] |= t), (n &= ~o);
  }
}
var A = 0;
function Gc(e) {
  return (e &= -e), 1 < e ? (4 < e ? (e & 268435455 ? 16 : 536870912) : 4) : 1;
}
var Yc,
  ks,
  Kc,
  Xc,
  Zc,
  kl = !1,
  Jr = [],
  Lt = null,
  It = null,
  Ot = null,
  kr = new Map(),
  xr = new Map(),
  jt = [],
  pm =
    "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(
      " "
    );
function Ma(e, t) {
  switch (e) {
    case "focusin":
    case "focusout":
      Lt = null;
      break;
    case "dragenter":
    case "dragleave":
      It = null;
      break;
    case "mouseover":
    case "mouseout":
      Ot = null;
      break;
    case "pointerover":
    case "pointerout":
      kr.delete(t.pointerId);
      break;
    case "gotpointercapture":
    case "lostpointercapture":
      xr.delete(t.pointerId);
  }
}
function Yn(e, t, n, r, o, i) {
  return e === null || e.nativeEvent !== i
    ? ((e = {
        blockedOn: t,
        domEventName: n,
        eventSystemFlags: r,
        nativeEvent: i,
        targetContainers: [o],
      }),
      t !== null && ((t = Br(t)), t !== null && ks(t)),
      e)
    : ((e.eventSystemFlags |= r),
      (t = e.targetContainers),
      o !== null && t.indexOf(o) === -1 && t.push(o),
      e);
}
function mm(e, t, n, r, o) {
  switch (t) {
    case "focusin":
      return (Lt = Yn(Lt, e, t, n, r, o)), !0;
    case "dragenter":
      return (It = Yn(It, e, t, n, r, o)), !0;
    case "mouseover":
      return (Ot = Yn(Ot, e, t, n, r, o)), !0;
    case "pointerover":
      var i = o.pointerId;
      return kr.set(i, Yn(kr.get(i) || null, e, t, n, r, o)), !0;
    case "gotpointercapture":
      return (
        (i = o.pointerId), xr.set(i, Yn(xr.get(i) || null, e, t, n, r, o)), !0
      );
  }
  return !1;
}
function Jc(e) {
  var t = Kt(e.target);
  if (t !== null) {
    var n = sn(t);
    if (n !== null) {
      if (((t = n.tag), t === 13)) {
        if (((t = Ac(n)), t !== null)) {
          (e.blockedOn = t),
            Zc(e.priority, function () {
              Kc(n);
            });
          return;
        }
      } else if (t === 3 && n.stateNode.current.memoizedState.isDehydrated) {
        e.blockedOn = n.tag === 3 ? n.stateNode.containerInfo : null;
        return;
      }
    }
  }
  e.blockedOn = null;
}
function vo(e) {
  if (e.blockedOn !== null) return !1;
  for (var t = e.targetContainers; 0 < t.length; ) {
    var n = xl(e.domEventName, e.eventSystemFlags, t[0], e.nativeEvent);
    if (n === null) {
      n = e.nativeEvent;
      var r = new n.constructor(n.type, n);
      (yl = r), n.target.dispatchEvent(r), (yl = null);
    } else return (t = Br(n)), t !== null && ks(t), (e.blockedOn = n), !1;
    t.shift();
  }
  return !0;
}
function Da(e, t, n) {
  vo(e) && n.delete(t);
}
function hm() {
  (kl = !1),
    Lt !== null && vo(Lt) && (Lt = null),
    It !== null && vo(It) && (It = null),
    Ot !== null && vo(Ot) && (Ot = null),
    kr.forEach(Da),
    xr.forEach(Da);
}
function Kn(e, t) {
  e.blockedOn === t &&
    ((e.blockedOn = null),
    kl ||
      ((kl = !0),
      Ve.unstable_scheduleCallback(Ve.unstable_NormalPriority, hm)));
}
function Cr(e) {
  function t(o) {
    return Kn(o, e);
  }
  if (0 < Jr.length) {
    Kn(Jr[0], e);
    for (var n = 1; n < Jr.length; n++) {
      var r = Jr[n];
      r.blockedOn === e && (r.blockedOn = null);
    }
  }
  for (
    Lt !== null && Kn(Lt, e),
      It !== null && Kn(It, e),
      Ot !== null && Kn(Ot, e),
      kr.forEach(t),
      xr.forEach(t),
      n = 0;
    n < jt.length;
    n++
  )
    (r = jt[n]), r.blockedOn === e && (r.blockedOn = null);
  for (; 0 < jt.length && ((n = jt[0]), n.blockedOn === null); )
    Jc(n), n.blockedOn === null && jt.shift();
}
var Tn = xt.ReactCurrentBatchConfig,
  zo = !0;
function ym(e, t, n, r) {
  var o = A,
    i = Tn.transition;
  Tn.transition = null;
  try {
    (A = 1), xs(e, t, n, r);
  } finally {
    (A = o), (Tn.transition = i);
  }
}
function vm(e, t, n, r) {
  var o = A,
    i = Tn.transition;
  Tn.transition = null;
  try {
    (A = 4), xs(e, t, n, r);
  } finally {
    (A = o), (Tn.transition = i);
  }
}
function xs(e, t, n, r) {
  if (zo) {
    var o = xl(e, t, n, r);
    if (o === null) Vi(e, t, r, Lo, n), Ma(e, r);
    else if (mm(o, e, t, n, r)) r.stopPropagation();
    else if ((Ma(e, r), t & 4 && -1 < pm.indexOf(e))) {
      for (; o !== null; ) {
        var i = Br(o);
        if (
          (i !== null && Yc(i),
          (i = xl(e, t, n, r)),
          i === null && Vi(e, t, r, Lo, n),
          i === o)
        )
          break;
        o = i;
      }
      o !== null && r.stopPropagation();
    } else Vi(e, t, r, null, n);
  }
}
var Lo = null;
function xl(e, t, n, r) {
  if (((Lo = null), (e = gs(r)), (e = Kt(e)), e !== null))
    if (((t = sn(e)), t === null)) e = null;
    else if (((n = t.tag), n === 13)) {
      if (((e = Ac(t)), e !== null)) return e;
      e = null;
    } else if (n === 3) {
      if (t.stateNode.current.memoizedState.isDehydrated)
        return t.tag === 3 ? t.stateNode.containerInfo : null;
      e = null;
    } else t !== e && (e = null);
  return (Lo = e), null;
}
function qc(e) {
  switch (e) {
    case "cancel":
    case "click":
    case "close":
    case "contextmenu":
    case "copy":
    case "cut":
    case "auxclick":
    case "dblclick":
    case "dragend":
    case "dragstart":
    case "drop":
    case "focusin":
    case "focusout":
    case "input":
    case "invalid":
    case "keydown":
    case "keypress":
    case "keyup":
    case "mousedown":
    case "mouseup":
    case "paste":
    case "pause":
    case "play":
    case "pointercancel":
    case "pointerdown":
    case "pointerup":
    case "ratechange":
    case "reset":
    case "resize":
    case "seeked":
    case "submit":
    case "touchcancel":
    case "touchend":
    case "touchstart":
    case "volumechange":
    case "change":
    case "selectionchange":
    case "textInput":
    case "compositionstart":
    case "compositionend":
    case "compositionupdate":
    case "beforeblur":
    case "afterblur":
    case "beforeinput":
    case "blur":
    case "fullscreenchange":
    case "focus":
    case "hashchange":
    case "popstate":
    case "select":
    case "selectstart":
      return 1;
    case "drag":
    case "dragenter":
    case "dragexit":
    case "dragleave":
    case "dragover":
    case "mousemove":
    case "mouseout":
    case "mouseover":
    case "pointermove":
    case "pointerout":
    case "pointerover":
    case "scroll":
    case "toggle":
    case "touchmove":
    case "wheel":
    case "mouseenter":
    case "mouseleave":
    case "pointerenter":
    case "pointerleave":
      return 4;
    case "message":
      switch (om()) {
        case ws:
          return 1;
        case Hc:
          return 4;
        case To:
        case im:
          return 16;
        case bc:
          return 536870912;
        default:
          return 16;
      }
    default:
      return 16;
  }
}
var Rt = null,
  Cs = null,
  go = null;
function ef() {
  if (go) return go;
  var e,
    t = Cs,
    n = t.length,
    r,
    o = "value" in Rt ? Rt.value : Rt.textContent,
    i = o.length;
  for (e = 0; e < n && t[e] === o[e]; e++);
  var l = n - e;
  for (r = 1; r <= l && t[n - r] === o[i - r]; r++);
  return (go = o.slice(e, 1 < r ? 1 - r : void 0));
}
function wo(e) {
  var t = e.keyCode;
  return (
    "charCode" in e
      ? ((e = e.charCode), e === 0 && t === 13 && (e = 13))
      : (e = t),
    e === 10 && (e = 13),
    32 <= e || e === 13 ? e : 0
  );
}
function qr() {
  return !0;
}
function Va() {
  return !1;
}
function Be(e) {
  function t(n, r, o, i, l) {
    (this._reactName = n),
      (this._targetInst = o),
      (this.type = r),
      (this.nativeEvent = i),
      (this.target = l),
      (this.currentTarget = null);
    for (var s in e)
      e.hasOwnProperty(s) && ((n = e[s]), (this[s] = n ? n(i) : i[s]));
    return (
      (this.isDefaultPrevented = (
        i.defaultPrevented != null ? i.defaultPrevented : i.returnValue === !1
      )
        ? qr
        : Va),
      (this.isPropagationStopped = Va),
      this
    );
  }
  return (
    Z(t.prototype, {
      preventDefault: function () {
        this.defaultPrevented = !0;
        var n = this.nativeEvent;
        n &&
          (n.preventDefault
            ? n.preventDefault()
            : typeof n.returnValue != "unknown" && (n.returnValue = !1),
          (this.isDefaultPrevented = qr));
      },
      stopPropagation: function () {
        var n = this.nativeEvent;
        n &&
          (n.stopPropagation
            ? n.stopPropagation()
            : typeof n.cancelBubble != "unknown" && (n.cancelBubble = !0),
          (this.isPropagationStopped = qr));
      },
      persist: function () {},
      isPersistent: qr,
    }),
    t
  );
}
var Wn = {
    eventPhase: 0,
    bubbles: 0,
    cancelable: 0,
    timeStamp: function (e) {
      return e.timeStamp || Date.now();
    },
    defaultPrevented: 0,
    isTrusted: 0,
  },
  Es = Be(Wn),
  Ar = Z({}, Wn, { view: 0, detail: 0 }),
  gm = Be(Ar),
  Ti,
  Ri,
  Xn,
  qo = Z({}, Ar, {
    screenX: 0,
    screenY: 0,
    clientX: 0,
    clientY: 0,
    pageX: 0,
    pageY: 0,
    ctrlKey: 0,
    shiftKey: 0,
    altKey: 0,
    metaKey: 0,
    getModifierState: _s,
    button: 0,
    buttons: 0,
    relatedTarget: function (e) {
      return e.relatedTarget === void 0
        ? e.fromElement === e.srcElement
          ? e.toElement
          : e.fromElement
        : e.relatedTarget;
    },
    movementX: function (e) {
      return "movementX" in e
        ? e.movementX
        : (e !== Xn &&
            (Xn && e.type === "mousemove"
              ? ((Ti = e.screenX - Xn.screenX), (Ri = e.screenY - Xn.screenY))
              : (Ri = Ti = 0),
            (Xn = e)),
          Ti);
    },
    movementY: function (e) {
      return "movementY" in e ? e.movementY : Ri;
    },
  }),
  Aa = Be(qo),
  wm = Z({}, qo, { dataTransfer: 0 }),
  Sm = Be(wm),
  km = Z({}, Ar, { relatedTarget: 0 }),
  zi = Be(km),
  xm = Z({}, Wn, { animationName: 0, elapsedTime: 0, pseudoElement: 0 }),
  Cm = Be(xm),
  Em = Z({}, Wn, {
    clipboardData: function (e) {
      return "clipboardData" in e ? e.clipboardData : window.clipboardData;
    },
  }),
  _m = Be(Em),
  $m = Z({}, Wn, { data: 0 }),
  Ba = Be($m),
  Nm = {
    Esc: "Escape",
    Spacebar: " ",
    Left: "ArrowLeft",
    Up: "ArrowUp",
    Right: "ArrowRight",
    Down: "ArrowDown",
    Del: "Delete",
    Win: "OS",
    Menu: "ContextMenu",
    Apps: "ContextMenu",
    Scroll: "ScrollLock",
    MozPrintableKey: "Unidentified",
  },
  Pm = {
    8: "Backspace",
    9: "Tab",
    12: "Clear",
    13: "Enter",
    16: "Shift",
    17: "Control",
    18: "Alt",
    19: "Pause",
    20: "CapsLock",
    27: "Escape",
    32: " ",
    33: "PageUp",
    34: "PageDown",
    35: "End",
    36: "Home",
    37: "ArrowLeft",
    38: "ArrowUp",
    39: "ArrowRight",
    40: "ArrowDown",
    45: "Insert",
    46: "Delete",
    112: "F1",
    113: "F2",
    114: "F3",
    115: "F4",
    116: "F5",
    117: "F6",
    118: "F7",
    119: "F8",
    120: "F9",
    121: "F10",
    122: "F11",
    123: "F12",
    144: "NumLock",
    145: "ScrollLock",
    224: "Meta",
  },
  jm = {
    Alt: "altKey",
    Control: "ctrlKey",
    Meta: "metaKey",
    Shift: "shiftKey",
  };
function Tm(e) {
  var t = this.nativeEvent;
  return t.getModifierState ? t.getModifierState(e) : (e = jm[e]) ? !!t[e] : !1;
}
function _s() {
  return Tm;
}
var Rm = Z({}, Ar, {
    key: function (e) {
      if (e.key) {
        var t = Nm[e.key] || e.key;
        if (t !== "Unidentified") return t;
      }
      return e.type === "keypress"
        ? ((e = wo(e)), e === 13 ? "Enter" : String.fromCharCode(e))
        : e.type === "keydown" || e.type === "keyup"
        ? Pm[e.keyCode] || "Unidentified"
        : "";
    },
    code: 0,
    location: 0,
    ctrlKey: 0,
    shiftKey: 0,
    altKey: 0,
    metaKey: 0,
    repeat: 0,
    locale: 0,
    getModifierState: _s,
    charCode: function (e) {
      return e.type === "keypress" ? wo(e) : 0;
    },
    keyCode: function (e) {
      return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
    },
    which: function (e) {
      return e.type === "keypress"
        ? wo(e)
        : e.type === "keydown" || e.type === "keyup"
        ? e.keyCode
        : 0;
    },
  }),
  zm = Be(Rm),
  Lm = Z({}, qo, {
    pointerId: 0,
    width: 0,
    height: 0,
    pressure: 0,
    tangentialPressure: 0,
    tiltX: 0,
    tiltY: 0,
    twist: 0,
    pointerType: 0,
    isPrimary: 0,
  }),
  Wa = Be(Lm),
  Im = Z({}, Ar, {
    touches: 0,
    targetTouches: 0,
    changedTouches: 0,
    altKey: 0,
    metaKey: 0,
    ctrlKey: 0,
    shiftKey: 0,
    getModifierState: _s,
  }),
  Om = Be(Im),
  Fm = Z({}, Wn, { propertyName: 0, elapsedTime: 0, pseudoElement: 0 }),
  Mm = Be(Fm),
  Dm = Z({}, qo, {
    deltaX: function (e) {
      return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
    },
    deltaY: function (e) {
      return "deltaY" in e
        ? e.deltaY
        : "wheelDeltaY" in e
        ? -e.wheelDeltaY
        : "wheelDelta" in e
        ? -e.wheelDelta
        : 0;
    },
    deltaZ: 0,
    deltaMode: 0,
  }),
  Vm = Be(Dm),
  Am = [9, 13, 27, 32],
  $s = gt && "CompositionEvent" in window,
  fr = null;
gt && "documentMode" in document && (fr = document.documentMode);
var Bm = gt && "TextEvent" in window && !fr,
  tf = gt && (!$s || (fr && 8 < fr && 11 >= fr)),
  Ua = " ",
  Ha = !1;
function nf(e, t) {
  switch (e) {
    case "keyup":
      return Am.indexOf(t.keyCode) !== -1;
    case "keydown":
      return t.keyCode !== 229;
    case "keypress":
    case "mousedown":
    case "focusout":
      return !0;
    default:
      return !1;
  }
}
function rf(e) {
  return (e = e.detail), typeof e == "object" && "data" in e ? e.data : null;
}
var yn = !1;
function Wm(e, t) {
  switch (e) {
    case "compositionend":
      return rf(t);
    case "keypress":
      return t.which !== 32 ? null : ((Ha = !0), Ua);
    case "textInput":
      return (e = t.data), e === Ua && Ha ? null : e;
    default:
      return null;
  }
}
function Um(e, t) {
  if (yn)
    return e === "compositionend" || (!$s && nf(e, t))
      ? ((e = ef()), (go = Cs = Rt = null), (yn = !1), e)
      : null;
  switch (e) {
    case "paste":
      return null;
    case "keypress":
      if (!(t.ctrlKey || t.altKey || t.metaKey) || (t.ctrlKey && t.altKey)) {
        if (t.char && 1 < t.char.length) return t.char;
        if (t.which) return String.fromCharCode(t.which);
      }
      return null;
    case "compositionend":
      return tf && t.locale !== "ko" ? null : t.data;
    default:
      return null;
  }
}
var Hm = {
  color: !0,
  date: !0,
  datetime: !0,
  "datetime-local": !0,
  email: !0,
  month: !0,
  number: !0,
  password: !0,
  range: !0,
  search: !0,
  tel: !0,
  text: !0,
  time: !0,
  url: !0,
  week: !0,
};
function ba(e) {
  var t = e && e.nodeName && e.nodeName.toLowerCase();
  return t === "input" ? !!Hm[e.type] : t === "textarea";
}
function of(e, t, n, r) {
  Oc(r),
    (t = Io(t, "onChange")),
    0 < t.length &&
      ((n = new Es("onChange", "change", null, n, r)),
      e.push({ event: n, listeners: t }));
}
var dr = null,
  Er = null;
function bm(e) {
  yf(e, 0);
}
function ei(e) {
  var t = wn(e);
  if (Pc(t)) return e;
}
function Qm(e, t) {
  if (e === "change") return t;
}
var lf = !1;
if (gt) {
  var Li;
  if (gt) {
    var Ii = "oninput" in document;
    if (!Ii) {
      var Qa = document.createElement("div");
      Qa.setAttribute("oninput", "return;"),
        (Ii = typeof Qa.oninput == "function");
    }
    Li = Ii;
  } else Li = !1;
  lf = Li && (!document.documentMode || 9 < document.documentMode);
}
function Ga() {
  dr && (dr.detachEvent("onpropertychange", sf), (Er = dr = null));
}
function sf(e) {
  if (e.propertyName === "value" && ei(Er)) {
    var t = [];
    of(t, Er, e, gs(e)), Vc(bm, t);
  }
}
function Gm(e, t, n) {
  e === "focusin"
    ? (Ga(), (dr = t), (Er = n), dr.attachEvent("onpropertychange", sf))
    : e === "focusout" && Ga();
}
function Ym(e) {
  if (e === "selectionchange" || e === "keyup" || e === "keydown")
    return ei(Er);
}
function Km(e, t) {
  if (e === "click") return ei(t);
}
function Xm(e, t) {
  if (e === "input" || e === "change") return ei(t);
}
function Zm(e, t) {
  return (e === t && (e !== 0 || 1 / e === 1 / t)) || (e !== e && t !== t);
}
var lt = typeof Object.is == "function" ? Object.is : Zm;
function _r(e, t) {
  if (lt(e, t)) return !0;
  if (typeof e != "object" || e === null || typeof t != "object" || t === null)
    return !1;
  var n = Object.keys(e),
    r = Object.keys(t);
  if (n.length !== r.length) return !1;
  for (r = 0; r < n.length; r++) {
    var o = n[r];
    if (!ol.call(t, o) || !lt(e[o], t[o])) return !1;
  }
  return !0;
}
function Ya(e) {
  for (; e && e.firstChild; ) e = e.firstChild;
  return e;
}
function Ka(e, t) {
  var n = Ya(e);
  e = 0;
  for (var r; n; ) {
    if (n.nodeType === 3) {
      if (((r = e + n.textContent.length), e <= t && r >= t))
        return { node: n, offset: t - e };
      e = r;
    }
    e: {
      for (; n; ) {
        if (n.nextSibling) {
          n = n.nextSibling;
          break e;
        }
        n = n.parentNode;
      }
      n = void 0;
    }
    n = Ya(n);
  }
}
function af(e, t) {
  return e && t
    ? e === t
      ? !0
      : e && e.nodeType === 3
      ? !1
      : t && t.nodeType === 3
      ? af(e, t.parentNode)
      : "contains" in e
      ? e.contains(t)
      : e.compareDocumentPosition
      ? !!(e.compareDocumentPosition(t) & 16)
      : !1
    : !1;
}
function uf() {
  for (var e = window, t = No(); t instanceof e.HTMLIFrameElement; ) {
    try {
      var n = typeof t.contentWindow.location.href == "string";
    } catch {
      n = !1;
    }
    if (n) e = t.contentWindow;
    else break;
    t = No(e.document);
  }
  return t;
}
function Ns(e) {
  var t = e && e.nodeName && e.nodeName.toLowerCase();
  return (
    t &&
    ((t === "input" &&
      (e.type === "text" ||
        e.type === "search" ||
        e.type === "tel" ||
        e.type === "url" ||
        e.type === "password")) ||
      t === "textarea" ||
      e.contentEditable === "true")
  );
}
function Jm(e) {
  var t = uf(),
    n = e.focusedElem,
    r = e.selectionRange;
  if (
    t !== n &&
    n &&
    n.ownerDocument &&
    af(n.ownerDocument.documentElement, n)
  ) {
    if (r !== null && Ns(n)) {
      if (
        ((t = r.start),
        (e = r.end),
        e === void 0 && (e = t),
        "selectionStart" in n)
      )
        (n.selectionStart = t), (n.selectionEnd = Math.min(e, n.value.length));
      else if (
        ((e = ((t = n.ownerDocument || document) && t.defaultView) || window),
        e.getSelection)
      ) {
        e = e.getSelection();
        var o = n.textContent.length,
          i = Math.min(r.start, o);
        (r = r.end === void 0 ? i : Math.min(r.end, o)),
          !e.extend && i > r && ((o = r), (r = i), (i = o)),
          (o = Ka(n, i));
        var l = Ka(n, r);
        o &&
          l &&
          (e.rangeCount !== 1 ||
            e.anchorNode !== o.node ||
            e.anchorOffset !== o.offset ||
            e.focusNode !== l.node ||
            e.focusOffset !== l.offset) &&
          ((t = t.createRange()),
          t.setStart(o.node, o.offset),
          e.removeAllRanges(),
          i > r
            ? (e.addRange(t), e.extend(l.node, l.offset))
            : (t.setEnd(l.node, l.offset), e.addRange(t)));
      }
    }
    for (t = [], e = n; (e = e.parentNode); )
      e.nodeType === 1 &&
        t.push({ element: e, left: e.scrollLeft, top: e.scrollTop });
    for (typeof n.focus == "function" && n.focus(), n = 0; n < t.length; n++)
      (e = t[n]),
        (e.element.scrollLeft = e.left),
        (e.element.scrollTop = e.top);
  }
}
var qm = gt && "documentMode" in document && 11 >= document.documentMode,
  vn = null,
  Cl = null,
  pr = null,
  El = !1;
function Xa(e, t, n) {
  var r = n.window === n ? n.document : n.nodeType === 9 ? n : n.ownerDocument;
  El ||
    vn == null ||
    vn !== No(r) ||
    ((r = vn),
    "selectionStart" in r && Ns(r)
      ? (r = { start: r.selectionStart, end: r.selectionEnd })
      : ((r = (
          (r.ownerDocument && r.ownerDocument.defaultView) ||
          window
        ).getSelection()),
        (r = {
          anchorNode: r.anchorNode,
          anchorOffset: r.anchorOffset,
          focusNode: r.focusNode,
          focusOffset: r.focusOffset,
        })),
    (pr && _r(pr, r)) ||
      ((pr = r),
      (r = Io(Cl, "onSelect")),
      0 < r.length &&
        ((t = new Es("onSelect", "select", null, t, n)),
        e.push({ event: t, listeners: r }),
        (t.target = vn))));
}
function eo(e, t) {
  var n = {};
  return (
    (n[e.toLowerCase()] = t.toLowerCase()),
    (n["Webkit" + e] = "webkit" + t),
    (n["Moz" + e] = "moz" + t),
    n
  );
}
var gn = {
    animationend: eo("Animation", "AnimationEnd"),
    animationiteration: eo("Animation", "AnimationIteration"),
    animationstart: eo("Animation", "AnimationStart"),
    transitionend: eo("Transition", "TransitionEnd"),
  },
  Oi = {},
  cf = {};
gt &&
  ((cf = document.createElement("div").style),
  "AnimationEvent" in window ||
    (delete gn.animationend.animation,
    delete gn.animationiteration.animation,
    delete gn.animationstart.animation),
  "TransitionEvent" in window || delete gn.transitionend.transition);
function ti(e) {
  if (Oi[e]) return Oi[e];
  if (!gn[e]) return e;
  var t = gn[e],
    n;
  for (n in t) if (t.hasOwnProperty(n) && n in cf) return (Oi[e] = t[n]);
  return e;
}
var ff = ti("animationend"),
  df = ti("animationiteration"),
  pf = ti("animationstart"),
  mf = ti("transitionend"),
  hf = new Map(),
  Za =
    "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(
      " "
    );
function Ht(e, t) {
  hf.set(e, t), ln(t, [e]);
}
for (var Fi = 0; Fi < Za.length; Fi++) {
  var Mi = Za[Fi],
    eh = Mi.toLowerCase(),
    th = Mi[0].toUpperCase() + Mi.slice(1);
  Ht(eh, "on" + th);
}
Ht(ff, "onAnimationEnd");
Ht(df, "onAnimationIteration");
Ht(pf, "onAnimationStart");
Ht("dblclick", "onDoubleClick");
Ht("focusin", "onFocus");
Ht("focusout", "onBlur");
Ht(mf, "onTransitionEnd");
In("onMouseEnter", ["mouseout", "mouseover"]);
In("onMouseLeave", ["mouseout", "mouseover"]);
In("onPointerEnter", ["pointerout", "pointerover"]);
In("onPointerLeave", ["pointerout", "pointerover"]);
ln(
  "onChange",
  "change click focusin focusout input keydown keyup selectionchange".split(" ")
);
ln(
  "onSelect",
  "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(
    " "
  )
);
ln("onBeforeInput", ["compositionend", "keypress", "textInput", "paste"]);
ln(
  "onCompositionEnd",
  "compositionend focusout keydown keypress keyup mousedown".split(" ")
);
ln(
  "onCompositionStart",
  "compositionstart focusout keydown keypress keyup mousedown".split(" ")
);
ln(
  "onCompositionUpdate",
  "compositionupdate focusout keydown keypress keyup mousedown".split(" ")
);
var sr =
    "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(
      " "
    ),
  nh = new Set("cancel close invalid load scroll toggle".split(" ").concat(sr));
function Ja(e, t, n) {
  var r = e.type || "unknown-event";
  (e.currentTarget = n), em(r, t, void 0, e), (e.currentTarget = null);
}
function yf(e, t) {
  t = (t & 4) !== 0;
  for (var n = 0; n < e.length; n++) {
    var r = e[n],
      o = r.event;
    r = r.listeners;
    e: {
      var i = void 0;
      if (t)
        for (var l = r.length - 1; 0 <= l; l--) {
          var s = r[l],
            a = s.instance,
            u = s.currentTarget;
          if (((s = s.listener), a !== i && o.isPropagationStopped())) break e;
          Ja(o, s, u), (i = a);
        }
      else
        for (l = 0; l < r.length; l++) {
          if (
            ((s = r[l]),
            (a = s.instance),
            (u = s.currentTarget),
            (s = s.listener),
            a !== i && o.isPropagationStopped())
          )
            break e;
          Ja(o, s, u), (i = a);
        }
    }
  }
  if (jo) throw ((e = wl), (jo = !1), (wl = null), e);
}
function Q(e, t) {
  var n = t[jl];
  n === void 0 && (n = t[jl] = new Set());
  var r = e + "__bubble";
  n.has(r) || (vf(t, e, 2, !1), n.add(r));
}
function Di(e, t, n) {
  var r = 0;
  t && (r |= 4), vf(n, e, r, t);
}
var to = "_reactListening" + Math.random().toString(36).slice(2);
function $r(e) {
  if (!e[to]) {
    (e[to] = !0),
      Cc.forEach(function (n) {
        n !== "selectionchange" && (nh.has(n) || Di(n, !1, e), Di(n, !0, e));
      });
    var t = e.nodeType === 9 ? e : e.ownerDocument;
    t === null || t[to] || ((t[to] = !0), Di("selectionchange", !1, t));
  }
}
function vf(e, t, n, r) {
  switch (qc(t)) {
    case 1:
      var o = ym;
      break;
    case 4:
      o = vm;
      break;
    default:
      o = xs;
  }
  (n = o.bind(null, t, n, e)),
    (o = void 0),
    !gl ||
      (t !== "touchstart" && t !== "touchmove" && t !== "wheel") ||
      (o = !0),
    r
      ? o !== void 0
        ? e.addEventListener(t, n, { capture: !0, passive: o })
        : e.addEventListener(t, n, !0)
      : o !== void 0
      ? e.addEventListener(t, n, { passive: o })
      : e.addEventListener(t, n, !1);
}
function Vi(e, t, n, r, o) {
  var i = r;
  if (!(t & 1) && !(t & 2) && r !== null)
    e: for (;;) {
      if (r === null) return;
      var l = r.tag;
      if (l === 3 || l === 4) {
        var s = r.stateNode.containerInfo;
        if (s === o || (s.nodeType === 8 && s.parentNode === o)) break;
        if (l === 4)
          for (l = r.return; l !== null; ) {
            var a = l.tag;
            if (
              (a === 3 || a === 4) &&
              ((a = l.stateNode.containerInfo),
              a === o || (a.nodeType === 8 && a.parentNode === o))
            )
              return;
            l = l.return;
          }
        for (; s !== null; ) {
          if (((l = Kt(s)), l === null)) return;
          if (((a = l.tag), a === 5 || a === 6)) {
            r = i = l;
            continue e;
          }
          s = s.parentNode;
        }
      }
      r = r.return;
    }
  Vc(function () {
    var u = i,
      f = gs(n),
      d = [];
    e: {
      var h = hf.get(e);
      if (h !== void 0) {
        var g = Es,
          y = e;
        switch (e) {
          case "keypress":
            if (wo(n) === 0) break e;
          case "keydown":
          case "keyup":
            g = zm;
            break;
          case "focusin":
            (y = "focus"), (g = zi);
            break;
          case "focusout":
            (y = "blur"), (g = zi);
            break;
          case "beforeblur":
          case "afterblur":
            g = zi;
            break;
          case "click":
            if (n.button === 2) break e;
          case "auxclick":
          case "dblclick":
          case "mousedown":
          case "mousemove":
          case "mouseup":
          case "mouseout":
          case "mouseover":
          case "contextmenu":
            g = Aa;
            break;
          case "drag":
          case "dragend":
          case "dragenter":
          case "dragexit":
          case "dragleave":
          case "dragover":
          case "dragstart":
          case "drop":
            g = Sm;
            break;
          case "touchcancel":
          case "touchend":
          case "touchmove":
          case "touchstart":
            g = Om;
            break;
          case ff:
          case df:
          case pf:
            g = Cm;
            break;
          case mf:
            g = Mm;
            break;
          case "scroll":
            g = gm;
            break;
          case "wheel":
            g = Vm;
            break;
          case "copy":
          case "cut":
          case "paste":
            g = _m;
            break;
          case "gotpointercapture":
          case "lostpointercapture":
          case "pointercancel":
          case "pointerdown":
          case "pointermove":
          case "pointerout":
          case "pointerover":
          case "pointerup":
            g = Wa;
        }
        var v = (t & 4) !== 0,
          C = !v && e === "scroll",
          m = v ? (h !== null ? h + "Capture" : null) : h;
        v = [];
        for (var c = u, p; c !== null; ) {
          p = c;
          var S = p.stateNode;
          if (
            (p.tag === 5 &&
              S !== null &&
              ((p = S),
              m !== null && ((S = Sr(c, m)), S != null && v.push(Nr(c, S, p)))),
            C)
          )
            break;
          c = c.return;
        }
        0 < v.length &&
          ((h = new g(h, y, null, n, f)), d.push({ event: h, listeners: v }));
      }
    }
    if (!(t & 7)) {
      e: {
        if (
          ((h = e === "mouseover" || e === "pointerover"),
          (g = e === "mouseout" || e === "pointerout"),
          h &&
            n !== yl &&
            (y = n.relatedTarget || n.fromElement) &&
            (Kt(y) || y[wt]))
        )
          break e;
        if (
          (g || h) &&
          ((h =
            f.window === f
              ? f
              : (h = f.ownerDocument)
              ? h.defaultView || h.parentWindow
              : window),
          g
            ? ((y = n.relatedTarget || n.toElement),
              (g = u),
              (y = y ? Kt(y) : null),
              y !== null &&
                ((C = sn(y)), y !== C || (y.tag !== 5 && y.tag !== 6)) &&
                (y = null))
            : ((g = null), (y = u)),
          g !== y)
        ) {
          if (
            ((v = Aa),
            (S = "onMouseLeave"),
            (m = "onMouseEnter"),
            (c = "mouse"),
            (e === "pointerout" || e === "pointerover") &&
              ((v = Wa),
              (S = "onPointerLeave"),
              (m = "onPointerEnter"),
              (c = "pointer")),
            (C = g == null ? h : wn(g)),
            (p = y == null ? h : wn(y)),
            (h = new v(S, c + "leave", g, n, f)),
            (h.target = C),
            (h.relatedTarget = p),
            (S = null),
            Kt(f) === u &&
              ((v = new v(m, c + "enter", y, n, f)),
              (v.target = p),
              (v.relatedTarget = C),
              (S = v)),
            (C = S),
            g && y)
          )
            t: {
              for (v = g, m = y, c = 0, p = v; p; p = cn(p)) c++;
              for (p = 0, S = m; S; S = cn(S)) p++;
              for (; 0 < c - p; ) (v = cn(v)), c--;
              for (; 0 < p - c; ) (m = cn(m)), p--;
              for (; c--; ) {
                if (v === m || (m !== null && v === m.alternate)) break t;
                (v = cn(v)), (m = cn(m));
              }
              v = null;
            }
          else v = null;
          g !== null && qa(d, h, g, v, !1),
            y !== null && C !== null && qa(d, C, y, v, !0);
        }
      }
      e: {
        if (
          ((h = u ? wn(u) : window),
          (g = h.nodeName && h.nodeName.toLowerCase()),
          g === "select" || (g === "input" && h.type === "file"))
        )
          var _ = Qm;
        else if (ba(h))
          if (lf) _ = Xm;
          else {
            _ = Ym;
            var w = Gm;
          }
        else
          (g = h.nodeName) &&
            g.toLowerCase() === "input" &&
            (h.type === "checkbox" || h.type === "radio") &&
            (_ = Km);
        if (_ && (_ = _(e, u))) {
          of(d, _, n, f);
          break e;
        }
        w && w(e, h, u),
          e === "focusout" &&
            (w = h._wrapperState) &&
            w.controlled &&
            h.type === "number" &&
            fl(h, "number", h.value);
      }
      switch (((w = u ? wn(u) : window), e)) {
        case "focusin":
          (ba(w) || w.contentEditable === "true") &&
            ((vn = w), (Cl = u), (pr = null));
          break;
        case "focusout":
          pr = Cl = vn = null;
          break;
        case "mousedown":
          El = !0;
          break;
        case "contextmenu":
        case "mouseup":
        case "dragend":
          (El = !1), Xa(d, n, f);
          break;
        case "selectionchange":
          if (qm) break;
        case "keydown":
        case "keyup":
          Xa(d, n, f);
      }
      var E;
      if ($s)
        e: {
          switch (e) {
            case "compositionstart":
              var N = "onCompositionStart";
              break e;
            case "compositionend":
              N = "onCompositionEnd";
              break e;
            case "compositionupdate":
              N = "onCompositionUpdate";
              break e;
          }
          N = void 0;
        }
      else
        yn
          ? nf(e, n) && (N = "onCompositionEnd")
          : e === "keydown" && n.keyCode === 229 && (N = "onCompositionStart");
      N &&
        (tf &&
          n.locale !== "ko" &&
          (yn || N !== "onCompositionStart"
            ? N === "onCompositionEnd" && yn && (E = ef())
            : ((Rt = f),
              (Cs = "value" in Rt ? Rt.value : Rt.textContent),
              (yn = !0))),
        (w = Io(u, N)),
        0 < w.length &&
          ((N = new Ba(N, e, null, n, f)),
          d.push({ event: N, listeners: w }),
          E ? (N.data = E) : ((E = rf(n)), E !== null && (N.data = E)))),
        (E = Bm ? Wm(e, n) : Um(e, n)) &&
          ((u = Io(u, "onBeforeInput")),
          0 < u.length &&
            ((f = new Ba("onBeforeInput", "beforeinput", null, n, f)),
            d.push({ event: f, listeners: u }),
            (f.data = E)));
    }
    yf(d, t);
  });
}
function Nr(e, t, n) {
  return { instance: e, listener: t, currentTarget: n };
}
function Io(e, t) {
  for (var n = t + "Capture", r = []; e !== null; ) {
    var o = e,
      i = o.stateNode;
    o.tag === 5 &&
      i !== null &&
      ((o = i),
      (i = Sr(e, n)),
      i != null && r.unshift(Nr(e, i, o)),
      (i = Sr(e, t)),
      i != null && r.push(Nr(e, i, o))),
      (e = e.return);
  }
  return r;
}
function cn(e) {
  if (e === null) return null;
  do e = e.return;
  while (e && e.tag !== 5);
  return e || null;
}
function qa(e, t, n, r, o) {
  for (var i = t._reactName, l = []; n !== null && n !== r; ) {
    var s = n,
      a = s.alternate,
      u = s.stateNode;
    if (a !== null && a === r) break;
    s.tag === 5 &&
      u !== null &&
      ((s = u),
      o
        ? ((a = Sr(n, i)), a != null && l.unshift(Nr(n, a, s)))
        : o || ((a = Sr(n, i)), a != null && l.push(Nr(n, a, s)))),
      (n = n.return);
  }
  l.length !== 0 && e.push({ event: t, listeners: l });
}
var rh = /\r\n?/g,
  oh = /\u0000|\uFFFD/g;
function eu(e) {
  return (typeof e == "string" ? e : "" + e)
    .replace(
      rh,
      `
`
    )
    .replace(oh, "");
}
function no(e, t, n) {
  if (((t = eu(t)), eu(e) !== t && n)) throw Error(P(425));
}
function Oo() {}
var _l = null,
  $l = null;
function Nl(e, t) {
  return (
    e === "textarea" ||
    e === "noscript" ||
    typeof t.children == "string" ||
    typeof t.children == "number" ||
    (typeof t.dangerouslySetInnerHTML == "object" &&
      t.dangerouslySetInnerHTML !== null &&
      t.dangerouslySetInnerHTML.__html != null)
  );
}
var Pl = typeof setTimeout == "function" ? setTimeout : void 0,
  ih = typeof clearTimeout == "function" ? clearTimeout : void 0,
  tu = typeof Promise == "function" ? Promise : void 0,
  lh =
    typeof queueMicrotask == "function"
      ? queueMicrotask
      : typeof tu < "u"
      ? function (e) {
          return tu.resolve(null).then(e).catch(sh);
        }
      : Pl;
function sh(e) {
  setTimeout(function () {
    throw e;
  });
}
function Ai(e, t) {
  var n = t,
    r = 0;
  do {
    var o = n.nextSibling;
    if ((e.removeChild(n), o && o.nodeType === 8))
      if (((n = o.data), n === "/$")) {
        if (r === 0) {
          e.removeChild(o), Cr(t);
          return;
        }
        r--;
      } else (n !== "$" && n !== "$?" && n !== "$!") || r++;
    n = o;
  } while (n);
  Cr(t);
}
function Ft(e) {
  for (; e != null; e = e.nextSibling) {
    var t = e.nodeType;
    if (t === 1 || t === 3) break;
    if (t === 8) {
      if (((t = e.data), t === "$" || t === "$!" || t === "$?")) break;
      if (t === "/$") return null;
    }
  }
  return e;
}
function nu(e) {
  e = e.previousSibling;
  for (var t = 0; e; ) {
    if (e.nodeType === 8) {
      var n = e.data;
      if (n === "$" || n === "$!" || n === "$?") {
        if (t === 0) return e;
        t--;
      } else n === "/$" && t++;
    }
    e = e.previousSibling;
  }
  return null;
}
var Un = Math.random().toString(36).slice(2),
  ut = "__reactFiber$" + Un,
  Pr = "__reactProps$" + Un,
  wt = "__reactContainer$" + Un,
  jl = "__reactEvents$" + Un,
  ah = "__reactListeners$" + Un,
  uh = "__reactHandles$" + Un;
function Kt(e) {
  var t = e[ut];
  if (t) return t;
  for (var n = e.parentNode; n; ) {
    if ((t = n[wt] || n[ut])) {
      if (
        ((n = t.alternate),
        t.child !== null || (n !== null && n.child !== null))
      )
        for (e = nu(e); e !== null; ) {
          if ((n = e[ut])) return n;
          e = nu(e);
        }
      return t;
    }
    (e = n), (n = e.parentNode);
  }
  return null;
}
function Br(e) {
  return (
    (e = e[ut] || e[wt]),
    !e || (e.tag !== 5 && e.tag !== 6 && e.tag !== 13 && e.tag !== 3) ? null : e
  );
}
function wn(e) {
  if (e.tag === 5 || e.tag === 6) return e.stateNode;
  throw Error(P(33));
}
function ni(e) {
  return e[Pr] || null;
}
var Tl = [],
  Sn = -1;
function bt(e) {
  return { current: e };
}
function G(e) {
  0 > Sn || ((e.current = Tl[Sn]), (Tl[Sn] = null), Sn--);
}
function U(e, t) {
  Sn++, (Tl[Sn] = e.current), (e.current = t);
}
var Wt = {},
  xe = bt(Wt),
  ze = bt(!1),
  en = Wt;
function On(e, t) {
  var n = e.type.contextTypes;
  if (!n) return Wt;
  var r = e.stateNode;
  if (r && r.__reactInternalMemoizedUnmaskedChildContext === t)
    return r.__reactInternalMemoizedMaskedChildContext;
  var o = {},
    i;
  for (i in n) o[i] = t[i];
  return (
    r &&
      ((e = e.stateNode),
      (e.__reactInternalMemoizedUnmaskedChildContext = t),
      (e.__reactInternalMemoizedMaskedChildContext = o)),
    o
  );
}
function Le(e) {
  return (e = e.childContextTypes), e != null;
}
function Fo() {
  G(ze), G(xe);
}
function ru(e, t, n) {
  if (xe.current !== Wt) throw Error(P(168));
  U(xe, t), U(ze, n);
}
function gf(e, t, n) {
  var r = e.stateNode;
  if (((t = t.childContextTypes), typeof r.getChildContext != "function"))
    return n;
  r = r.getChildContext();
  for (var o in r) if (!(o in t)) throw Error(P(108, Gp(e) || "Unknown", o));
  return Z({}, n, r);
}
function Mo(e) {
  return (
    (e =
      ((e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext) || Wt),
    (en = xe.current),
    U(xe, e),
    U(ze, ze.current),
    !0
  );
}
function ou(e, t, n) {
  var r = e.stateNode;
  if (!r) throw Error(P(169));
  n
    ? ((e = gf(e, t, en)),
      (r.__reactInternalMemoizedMergedChildContext = e),
      G(ze),
      G(xe),
      U(xe, e))
    : G(ze),
    U(ze, n);
}
var mt = null,
  ri = !1,
  Bi = !1;
function wf(e) {
  mt === null ? (mt = [e]) : mt.push(e);
}
function ch(e) {
  (ri = !0), wf(e);
}
function Qt() {
  if (!Bi && mt !== null) {
    Bi = !0;
    var e = 0,
      t = A;
    try {
      var n = mt;
      for (A = 1; e < n.length; e++) {
        var r = n[e];
        do r = r(!0);
        while (r !== null);
      }
      (mt = null), (ri = !1);
    } catch (o) {
      throw (mt !== null && (mt = mt.slice(e + 1)), Uc(ws, Qt), o);
    } finally {
      (A = t), (Bi = !1);
    }
  }
  return null;
}
var kn = [],
  xn = 0,
  Do = null,
  Vo = 0,
  We = [],
  Ue = 0,
  tn = null,
  ht = 1,
  yt = "";
function Gt(e, t) {
  (kn[xn++] = Vo), (kn[xn++] = Do), (Do = e), (Vo = t);
}
function Sf(e, t, n) {
  (We[Ue++] = ht), (We[Ue++] = yt), (We[Ue++] = tn), (tn = e);
  var r = ht;
  e = yt;
  var o = 32 - rt(r) - 1;
  (r &= ~(1 << o)), (n += 1);
  var i = 32 - rt(t) + o;
  if (30 < i) {
    var l = o - (o % 5);
    (i = (r & ((1 << l) - 1)).toString(32)),
      (r >>= l),
      (o -= l),
      (ht = (1 << (32 - rt(t) + o)) | (n << o) | r),
      (yt = i + e);
  } else (ht = (1 << i) | (n << o) | r), (yt = e);
}
function Ps(e) {
  e.return !== null && (Gt(e, 1), Sf(e, 1, 0));
}
function js(e) {
  for (; e === Do; )
    (Do = kn[--xn]), (kn[xn] = null), (Vo = kn[--xn]), (kn[xn] = null);
  for (; e === tn; )
    (tn = We[--Ue]),
      (We[Ue] = null),
      (yt = We[--Ue]),
      (We[Ue] = null),
      (ht = We[--Ue]),
      (We[Ue] = null);
}
var De = null,
  Me = null,
  Y = !1,
  et = null;
function kf(e, t) {
  var n = He(5, null, null, 0);
  (n.elementType = "DELETED"),
    (n.stateNode = t),
    (n.return = e),
    (t = e.deletions),
    t === null ? ((e.deletions = [n]), (e.flags |= 16)) : t.push(n);
}
function iu(e, t) {
  switch (e.tag) {
    case 5:
      var n = e.type;
      return (
        (t =
          t.nodeType !== 1 || n.toLowerCase() !== t.nodeName.toLowerCase()
            ? null
            : t),
        t !== null
          ? ((e.stateNode = t), (De = e), (Me = Ft(t.firstChild)), !0)
          : !1
      );
    case 6:
      return (
        (t = e.pendingProps === "" || t.nodeType !== 3 ? null : t),
        t !== null ? ((e.stateNode = t), (De = e), (Me = null), !0) : !1
      );
    case 13:
      return (
        (t = t.nodeType !== 8 ? null : t),
        t !== null
          ? ((n = tn !== null ? { id: ht, overflow: yt } : null),
            (e.memoizedState = {
              dehydrated: t,
              treeContext: n,
              retryLane: 1073741824,
            }),
            (n = He(18, null, null, 0)),
            (n.stateNode = t),
            (n.return = e),
            (e.child = n),
            (De = e),
            (Me = null),
            !0)
          : !1
      );
    default:
      return !1;
  }
}
function Rl(e) {
  return (e.mode & 1) !== 0 && (e.flags & 128) === 0;
}
function zl(e) {
  if (Y) {
    var t = Me;
    if (t) {
      var n = t;
      if (!iu(e, t)) {
        if (Rl(e)) throw Error(P(418));
        t = Ft(n.nextSibling);
        var r = De;
        t && iu(e, t)
          ? kf(r, n)
          : ((e.flags = (e.flags & -4097) | 2), (Y = !1), (De = e));
      }
    } else {
      if (Rl(e)) throw Error(P(418));
      (e.flags = (e.flags & -4097) | 2), (Y = !1), (De = e);
    }
  }
}
function lu(e) {
  for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13; )
    e = e.return;
  De = e;
}
function ro(e) {
  if (e !== De) return !1;
  if (!Y) return lu(e), (Y = !0), !1;
  var t;
  if (
    ((t = e.tag !== 3) &&
      !(t = e.tag !== 5) &&
      ((t = e.type),
      (t = t !== "head" && t !== "body" && !Nl(e.type, e.memoizedProps))),
    t && (t = Me))
  ) {
    if (Rl(e)) throw (xf(), Error(P(418)));
    for (; t; ) kf(e, t), (t = Ft(t.nextSibling));
  }
  if ((lu(e), e.tag === 13)) {
    if (((e = e.memoizedState), (e = e !== null ? e.dehydrated : null), !e))
      throw Error(P(317));
    e: {
      for (e = e.nextSibling, t = 0; e; ) {
        if (e.nodeType === 8) {
          var n = e.data;
          if (n === "/$") {
            if (t === 0) {
              Me = Ft(e.nextSibling);
              break e;
            }
            t--;
          } else (n !== "$" && n !== "$!" && n !== "$?") || t++;
        }
        e = e.nextSibling;
      }
      Me = null;
    }
  } else Me = De ? Ft(e.stateNode.nextSibling) : null;
  return !0;
}
function xf() {
  for (var e = Me; e; ) e = Ft(e.nextSibling);
}
function Fn() {
  (Me = De = null), (Y = !1);
}
function Ts(e) {
  et === null ? (et = [e]) : et.push(e);
}
var fh = xt.ReactCurrentBatchConfig;
function Zn(e, t, n) {
  if (
    ((e = n.ref), e !== null && typeof e != "function" && typeof e != "object")
  ) {
    if (n._owner) {
      if (((n = n._owner), n)) {
        if (n.tag !== 1) throw Error(P(309));
        var r = n.stateNode;
      }
      if (!r) throw Error(P(147, e));
      var o = r,
        i = "" + e;
      return t !== null &&
        t.ref !== null &&
        typeof t.ref == "function" &&
        t.ref._stringRef === i
        ? t.ref
        : ((t = function (l) {
            var s = o.refs;
            l === null ? delete s[i] : (s[i] = l);
          }),
          (t._stringRef = i),
          t);
    }
    if (typeof e != "string") throw Error(P(284));
    if (!n._owner) throw Error(P(290, e));
  }
  return e;
}
function oo(e, t) {
  throw (
    ((e = Object.prototype.toString.call(t)),
    Error(
      P(
        31,
        e === "[object Object]"
          ? "object with keys {" + Object.keys(t).join(", ") + "}"
          : e
      )
    ))
  );
}
function su(e) {
  var t = e._init;
  return t(e._payload);
}
function Cf(e) {
  function t(m, c) {
    if (e) {
      var p = m.deletions;
      p === null ? ((m.deletions = [c]), (m.flags |= 16)) : p.push(c);
    }
  }
  function n(m, c) {
    if (!e) return null;
    for (; c !== null; ) t(m, c), (c = c.sibling);
    return null;
  }
  function r(m, c) {
    for (m = new Map(); c !== null; )
      c.key !== null ? m.set(c.key, c) : m.set(c.index, c), (c = c.sibling);
    return m;
  }
  function o(m, c) {
    return (m = At(m, c)), (m.index = 0), (m.sibling = null), m;
  }
  function i(m, c, p) {
    return (
      (m.index = p),
      e
        ? ((p = m.alternate),
          p !== null
            ? ((p = p.index), p < c ? ((m.flags |= 2), c) : p)
            : ((m.flags |= 2), c))
        : ((m.flags |= 1048576), c)
    );
  }
  function l(m) {
    return e && m.alternate === null && (m.flags |= 2), m;
  }
  function s(m, c, p, S) {
    return c === null || c.tag !== 6
      ? ((c = Yi(p, m.mode, S)), (c.return = m), c)
      : ((c = o(c, p)), (c.return = m), c);
  }
  function a(m, c, p, S) {
    var _ = p.type;
    return _ === hn
      ? f(m, c, p.props.children, S, p.key)
      : c !== null &&
        (c.elementType === _ ||
          (typeof _ == "object" &&
            _ !== null &&
            _.$$typeof === Nt &&
            su(_) === c.type))
      ? ((S = o(c, p.props)), (S.ref = Zn(m, c, p)), (S.return = m), S)
      : ((S = $o(p.type, p.key, p.props, null, m.mode, S)),
        (S.ref = Zn(m, c, p)),
        (S.return = m),
        S);
  }
  function u(m, c, p, S) {
    return c === null ||
      c.tag !== 4 ||
      c.stateNode.containerInfo !== p.containerInfo ||
      c.stateNode.implementation !== p.implementation
      ? ((c = Ki(p, m.mode, S)), (c.return = m), c)
      : ((c = o(c, p.children || [])), (c.return = m), c);
  }
  function f(m, c, p, S, _) {
    return c === null || c.tag !== 7
      ? ((c = qt(p, m.mode, S, _)), (c.return = m), c)
      : ((c = o(c, p)), (c.return = m), c);
  }
  function d(m, c, p) {
    if ((typeof c == "string" && c !== "") || typeof c == "number")
      return (c = Yi("" + c, m.mode, p)), (c.return = m), c;
    if (typeof c == "object" && c !== null) {
      switch (c.$$typeof) {
        case Gr:
          return (
            (p = $o(c.type, c.key, c.props, null, m.mode, p)),
            (p.ref = Zn(m, null, c)),
            (p.return = m),
            p
          );
        case mn:
          return (c = Ki(c, m.mode, p)), (c.return = m), c;
        case Nt:
          var S = c._init;
          return d(m, S(c._payload), p);
      }
      if (ir(c) || Qn(c))
        return (c = qt(c, m.mode, p, null)), (c.return = m), c;
      oo(m, c);
    }
    return null;
  }
  function h(m, c, p, S) {
    var _ = c !== null ? c.key : null;
    if ((typeof p == "string" && p !== "") || typeof p == "number")
      return _ !== null ? null : s(m, c, "" + p, S);
    if (typeof p == "object" && p !== null) {
      switch (p.$$typeof) {
        case Gr:
          return p.key === _ ? a(m, c, p, S) : null;
        case mn:
          return p.key === _ ? u(m, c, p, S) : null;
        case Nt:
          return (_ = p._init), h(m, c, _(p._payload), S);
      }
      if (ir(p) || Qn(p)) return _ !== null ? null : f(m, c, p, S, null);
      oo(m, p);
    }
    return null;
  }
  function g(m, c, p, S, _) {
    if ((typeof S == "string" && S !== "") || typeof S == "number")
      return (m = m.get(p) || null), s(c, m, "" + S, _);
    if (typeof S == "object" && S !== null) {
      switch (S.$$typeof) {
        case Gr:
          return (m = m.get(S.key === null ? p : S.key) || null), a(c, m, S, _);
        case mn:
          return (m = m.get(S.key === null ? p : S.key) || null), u(c, m, S, _);
        case Nt:
          var w = S._init;
          return g(m, c, p, w(S._payload), _);
      }
      if (ir(S) || Qn(S)) return (m = m.get(p) || null), f(c, m, S, _, null);
      oo(c, S);
    }
    return null;
  }
  function y(m, c, p, S) {
    for (
      var _ = null, w = null, E = c, N = (c = 0), I = null;
      E !== null && N < p.length;
      N++
    ) {
      E.index > N ? ((I = E), (E = null)) : (I = E.sibling);
      var O = h(m, E, p[N], S);
      if (O === null) {
        E === null && (E = I);
        break;
      }
      e && E && O.alternate === null && t(m, E),
        (c = i(O, c, N)),
        w === null ? (_ = O) : (w.sibling = O),
        (w = O),
        (E = I);
    }
    if (N === p.length) return n(m, E), Y && Gt(m, N), _;
    if (E === null) {
      for (; N < p.length; N++)
        (E = d(m, p[N], S)),
          E !== null &&
            ((c = i(E, c, N)), w === null ? (_ = E) : (w.sibling = E), (w = E));
      return Y && Gt(m, N), _;
    }
    for (E = r(m, E); N < p.length; N++)
      (I = g(E, m, N, p[N], S)),
        I !== null &&
          (e && I.alternate !== null && E.delete(I.key === null ? N : I.key),
          (c = i(I, c, N)),
          w === null ? (_ = I) : (w.sibling = I),
          (w = I));
    return (
      e &&
        E.forEach(function (b) {
          return t(m, b);
        }),
      Y && Gt(m, N),
      _
    );
  }
  function v(m, c, p, S) {
    var _ = Qn(p);
    if (typeof _ != "function") throw Error(P(150));
    if (((p = _.call(p)), p == null)) throw Error(P(151));
    for (
      var w = (_ = null), E = c, N = (c = 0), I = null, O = p.next();
      E !== null && !O.done;
      N++, O = p.next()
    ) {
      E.index > N ? ((I = E), (E = null)) : (I = E.sibling);
      var b = h(m, E, O.value, S);
      if (b === null) {
        E === null && (E = I);
        break;
      }
      e && E && b.alternate === null && t(m, E),
        (c = i(b, c, N)),
        w === null ? (_ = b) : (w.sibling = b),
        (w = b),
        (E = I);
    }
    if (O.done) return n(m, E), Y && Gt(m, N), _;
    if (E === null) {
      for (; !O.done; N++, O = p.next())
        (O = d(m, O.value, S)),
          O !== null &&
            ((c = i(O, c, N)), w === null ? (_ = O) : (w.sibling = O), (w = O));
      return Y && Gt(m, N), _;
    }
    for (E = r(m, E); !O.done; N++, O = p.next())
      (O = g(E, m, N, O.value, S)),
        O !== null &&
          (e && O.alternate !== null && E.delete(O.key === null ? N : O.key),
          (c = i(O, c, N)),
          w === null ? (_ = O) : (w.sibling = O),
          (w = O));
    return (
      e &&
        E.forEach(function (ie) {
          return t(m, ie);
        }),
      Y && Gt(m, N),
      _
    );
  }
  function C(m, c, p, S) {
    if (
      (typeof p == "object" &&
        p !== null &&
        p.type === hn &&
        p.key === null &&
        (p = p.props.children),
      typeof p == "object" && p !== null)
    ) {
      switch (p.$$typeof) {
        case Gr:
          e: {
            for (var _ = p.key, w = c; w !== null; ) {
              if (w.key === _) {
                if (((_ = p.type), _ === hn)) {
                  if (w.tag === 7) {
                    n(m, w.sibling),
                      (c = o(w, p.props.children)),
                      (c.return = m),
                      (m = c);
                    break e;
                  }
                } else if (
                  w.elementType === _ ||
                  (typeof _ == "object" &&
                    _ !== null &&
                    _.$$typeof === Nt &&
                    su(_) === w.type)
                ) {
                  n(m, w.sibling),
                    (c = o(w, p.props)),
                    (c.ref = Zn(m, w, p)),
                    (c.return = m),
                    (m = c);
                  break e;
                }
                n(m, w);
                break;
              } else t(m, w);
              w = w.sibling;
            }
            p.type === hn
              ? ((c = qt(p.props.children, m.mode, S, p.key)),
                (c.return = m),
                (m = c))
              : ((S = $o(p.type, p.key, p.props, null, m.mode, S)),
                (S.ref = Zn(m, c, p)),
                (S.return = m),
                (m = S));
          }
          return l(m);
        case mn:
          e: {
            for (w = p.key; c !== null; ) {
              if (c.key === w)
                if (
                  c.tag === 4 &&
                  c.stateNode.containerInfo === p.containerInfo &&
                  c.stateNode.implementation === p.implementation
                ) {
                  n(m, c.sibling),
                    (c = o(c, p.children || [])),
                    (c.return = m),
                    (m = c);
                  break e;
                } else {
                  n(m, c);
                  break;
                }
              else t(m, c);
              c = c.sibling;
            }
            (c = Ki(p, m.mode, S)), (c.return = m), (m = c);
          }
          return l(m);
        case Nt:
          return (w = p._init), C(m, c, w(p._payload), S);
      }
      if (ir(p)) return y(m, c, p, S);
      if (Qn(p)) return v(m, c, p, S);
      oo(m, p);
    }
    return (typeof p == "string" && p !== "") || typeof p == "number"
      ? ((p = "" + p),
        c !== null && c.tag === 6
          ? (n(m, c.sibling), (c = o(c, p)), (c.return = m), (m = c))
          : (n(m, c), (c = Yi(p, m.mode, S)), (c.return = m), (m = c)),
        l(m))
      : n(m, c);
  }
  return C;
}
var Mn = Cf(!0),
  Ef = Cf(!1),
  Ao = bt(null),
  Bo = null,
  Cn = null,
  Rs = null;
function zs() {
  Rs = Cn = Bo = null;
}
function Ls(e) {
  var t = Ao.current;
  G(Ao), (e._currentValue = t);
}
function Ll(e, t, n) {
  for (; e !== null; ) {
    var r = e.alternate;
    if (
      ((e.childLanes & t) !== t
        ? ((e.childLanes |= t), r !== null && (r.childLanes |= t))
        : r !== null && (r.childLanes & t) !== t && (r.childLanes |= t),
      e === n)
    )
      break;
    e = e.return;
  }
}
function Rn(e, t) {
  (Bo = e),
    (Rs = Cn = null),
    (e = e.dependencies),
    e !== null &&
      e.firstContext !== null &&
      (e.lanes & t && (Re = !0), (e.firstContext = null));
}
function Qe(e) {
  var t = e._currentValue;
  if (Rs !== e)
    if (((e = { context: e, memoizedValue: t, next: null }), Cn === null)) {
      if (Bo === null) throw Error(P(308));
      (Cn = e), (Bo.dependencies = { lanes: 0, firstContext: e });
    } else Cn = Cn.next = e;
  return t;
}
var Xt = null;
function Is(e) {
  Xt === null ? (Xt = [e]) : Xt.push(e);
}
function _f(e, t, n, r) {
  var o = t.interleaved;
  return (
    o === null ? ((n.next = n), Is(t)) : ((n.next = o.next), (o.next = n)),
    (t.interleaved = n),
    St(e, r)
  );
}
function St(e, t) {
  e.lanes |= t;
  var n = e.alternate;
  for (n !== null && (n.lanes |= t), n = e, e = e.return; e !== null; )
    (e.childLanes |= t),
      (n = e.alternate),
      n !== null && (n.childLanes |= t),
      (n = e),
      (e = e.return);
  return n.tag === 3 ? n.stateNode : null;
}
var Pt = !1;
function Os(e) {
  e.updateQueue = {
    baseState: e.memoizedState,
    firstBaseUpdate: null,
    lastBaseUpdate: null,
    shared: { pending: null, interleaved: null, lanes: 0 },
    effects: null,
  };
}
function $f(e, t) {
  (e = e.updateQueue),
    t.updateQueue === e &&
      (t.updateQueue = {
        baseState: e.baseState,
        firstBaseUpdate: e.firstBaseUpdate,
        lastBaseUpdate: e.lastBaseUpdate,
        shared: e.shared,
        effects: e.effects,
      });
}
function vt(e, t) {
  return {
    eventTime: e,
    lane: t,
    tag: 0,
    payload: null,
    callback: null,
    next: null,
  };
}
function Mt(e, t, n) {
  var r = e.updateQueue;
  if (r === null) return null;
  if (((r = r.shared), D & 2)) {
    var o = r.pending;
    return (
      o === null ? (t.next = t) : ((t.next = o.next), (o.next = t)),
      (r.pending = t),
      St(e, n)
    );
  }
  return (
    (o = r.interleaved),
    o === null ? ((t.next = t), Is(r)) : ((t.next = o.next), (o.next = t)),
    (r.interleaved = t),
    St(e, n)
  );
}
function So(e, t, n) {
  if (
    ((t = t.updateQueue), t !== null && ((t = t.shared), (n & 4194240) !== 0))
  ) {
    var r = t.lanes;
    (r &= e.pendingLanes), (n |= r), (t.lanes = n), Ss(e, n);
  }
}
function au(e, t) {
  var n = e.updateQueue,
    r = e.alternate;
  if (r !== null && ((r = r.updateQueue), n === r)) {
    var o = null,
      i = null;
    if (((n = n.firstBaseUpdate), n !== null)) {
      do {
        var l = {
          eventTime: n.eventTime,
          lane: n.lane,
          tag: n.tag,
          payload: n.payload,
          callback: n.callback,
          next: null,
        };
        i === null ? (o = i = l) : (i = i.next = l), (n = n.next);
      } while (n !== null);
      i === null ? (o = i = t) : (i = i.next = t);
    } else o = i = t;
    (n = {
      baseState: r.baseState,
      firstBaseUpdate: o,
      lastBaseUpdate: i,
      shared: r.shared,
      effects: r.effects,
    }),
      (e.updateQueue = n);
    return;
  }
  (e = n.lastBaseUpdate),
    e === null ? (n.firstBaseUpdate = t) : (e.next = t),
    (n.lastBaseUpdate = t);
}
function Wo(e, t, n, r) {
  var o = e.updateQueue;
  Pt = !1;
  var i = o.firstBaseUpdate,
    l = o.lastBaseUpdate,
    s = o.shared.pending;
  if (s !== null) {
    o.shared.pending = null;
    var a = s,
      u = a.next;
    (a.next = null), l === null ? (i = u) : (l.next = u), (l = a);
    var f = e.alternate;
    f !== null &&
      ((f = f.updateQueue),
      (s = f.lastBaseUpdate),
      s !== l &&
        (s === null ? (f.firstBaseUpdate = u) : (s.next = u),
        (f.lastBaseUpdate = a)));
  }
  if (i !== null) {
    var d = o.baseState;
    (l = 0), (f = u = a = null), (s = i);
    do {
      var h = s.lane,
        g = s.eventTime;
      if ((r & h) === h) {
        f !== null &&
          (f = f.next =
            {
              eventTime: g,
              lane: 0,
              tag: s.tag,
              payload: s.payload,
              callback: s.callback,
              next: null,
            });
        e: {
          var y = e,
            v = s;
          switch (((h = t), (g = n), v.tag)) {
            case 1:
              if (((y = v.payload), typeof y == "function")) {
                d = y.call(g, d, h);
                break e;
              }
              d = y;
              break e;
            case 3:
              y.flags = (y.flags & -65537) | 128;
            case 0:
              if (
                ((y = v.payload),
                (h = typeof y == "function" ? y.call(g, d, h) : y),
                h == null)
              )
                break e;
              d = Z({}, d, h);
              break e;
            case 2:
              Pt = !0;
          }
        }
        s.callback !== null &&
          s.lane !== 0 &&
          ((e.flags |= 64),
          (h = o.effects),
          h === null ? (o.effects = [s]) : h.push(s));
      } else
        (g = {
          eventTime: g,
          lane: h,
          tag: s.tag,
          payload: s.payload,
          callback: s.callback,
          next: null,
        }),
          f === null ? ((u = f = g), (a = d)) : (f = f.next = g),
          (l |= h);
      if (((s = s.next), s === null)) {
        if (((s = o.shared.pending), s === null)) break;
        (h = s),
          (s = h.next),
          (h.next = null),
          (o.lastBaseUpdate = h),
          (o.shared.pending = null);
      }
    } while (!0);
    if (
      (f === null && (a = d),
      (o.baseState = a),
      (o.firstBaseUpdate = u),
      (o.lastBaseUpdate = f),
      (t = o.shared.interleaved),
      t !== null)
    ) {
      o = t;
      do (l |= o.lane), (o = o.next);
      while (o !== t);
    } else i === null && (o.shared.lanes = 0);
    (rn |= l), (e.lanes = l), (e.memoizedState = d);
  }
}
function uu(e, t, n) {
  if (((e = t.effects), (t.effects = null), e !== null))
    for (t = 0; t < e.length; t++) {
      var r = e[t],
        o = r.callback;
      if (o !== null) {
        if (((r.callback = null), (r = n), typeof o != "function"))
          throw Error(P(191, o));
        o.call(r);
      }
    }
}
var Wr = {},
  ft = bt(Wr),
  jr = bt(Wr),
  Tr = bt(Wr);
function Zt(e) {
  if (e === Wr) throw Error(P(174));
  return e;
}
function Fs(e, t) {
  switch ((U(Tr, t), U(jr, e), U(ft, Wr), (e = t.nodeType), e)) {
    case 9:
    case 11:
      t = (t = t.documentElement) ? t.namespaceURI : pl(null, "");
      break;
    default:
      (e = e === 8 ? t.parentNode : t),
        (t = e.namespaceURI || null),
        (e = e.tagName),
        (t = pl(t, e));
  }
  G(ft), U(ft, t);
}
function Dn() {
  G(ft), G(jr), G(Tr);
}
function Nf(e) {
  Zt(Tr.current);
  var t = Zt(ft.current),
    n = pl(t, e.type);
  t !== n && (U(jr, e), U(ft, n));
}
function Ms(e) {
  jr.current === e && (G(ft), G(jr));
}
var K = bt(0);
function Uo(e) {
  for (var t = e; t !== null; ) {
    if (t.tag === 13) {
      var n = t.memoizedState;
      if (
        n !== null &&
        ((n = n.dehydrated), n === null || n.data === "$?" || n.data === "$!")
      )
        return t;
    } else if (t.tag === 19 && t.memoizedProps.revealOrder !== void 0) {
      if (t.flags & 128) return t;
    } else if (t.child !== null) {
      (t.child.return = t), (t = t.child);
      continue;
    }
    if (t === e) break;
    for (; t.sibling === null; ) {
      if (t.return === null || t.return === e) return null;
      t = t.return;
    }
    (t.sibling.return = t.return), (t = t.sibling);
  }
  return null;
}
var Wi = [];
function Ds() {
  for (var e = 0; e < Wi.length; e++)
    Wi[e]._workInProgressVersionPrimary = null;
  Wi.length = 0;
}
var ko = xt.ReactCurrentDispatcher,
  Ui = xt.ReactCurrentBatchConfig,
  nn = 0,
  X = null,
  re = null,
  se = null,
  Ho = !1,
  mr = !1,
  Rr = 0,
  dh = 0;
function ve() {
  throw Error(P(321));
}
function Vs(e, t) {
  if (t === null) return !1;
  for (var n = 0; n < t.length && n < e.length; n++)
    if (!lt(e[n], t[n])) return !1;
  return !0;
}
function As(e, t, n, r, o, i) {
  if (
    ((nn = i),
    (X = t),
    (t.memoizedState = null),
    (t.updateQueue = null),
    (t.lanes = 0),
    (ko.current = e === null || e.memoizedState === null ? yh : vh),
    (e = n(r, o)),
    mr)
  ) {
    i = 0;
    do {
      if (((mr = !1), (Rr = 0), 25 <= i)) throw Error(P(301));
      (i += 1),
        (se = re = null),
        (t.updateQueue = null),
        (ko.current = gh),
        (e = n(r, o));
    } while (mr);
  }
  if (
    ((ko.current = bo),
    (t = re !== null && re.next !== null),
    (nn = 0),
    (se = re = X = null),
    (Ho = !1),
    t)
  )
    throw Error(P(300));
  return e;
}
function Bs() {
  var e = Rr !== 0;
  return (Rr = 0), e;
}
function at() {
  var e = {
    memoizedState: null,
    baseState: null,
    baseQueue: null,
    queue: null,
    next: null,
  };
  return se === null ? (X.memoizedState = se = e) : (se = se.next = e), se;
}
function Ge() {
  if (re === null) {
    var e = X.alternate;
    e = e !== null ? e.memoizedState : null;
  } else e = re.next;
  var t = se === null ? X.memoizedState : se.next;
  if (t !== null) (se = t), (re = e);
  else {
    if (e === null) throw Error(P(310));
    (re = e),
      (e = {
        memoizedState: re.memoizedState,
        baseState: re.baseState,
        baseQueue: re.baseQueue,
        queue: re.queue,
        next: null,
      }),
      se === null ? (X.memoizedState = se = e) : (se = se.next = e);
  }
  return se;
}
function zr(e, t) {
  return typeof t == "function" ? t(e) : t;
}
function Hi(e) {
  var t = Ge(),
    n = t.queue;
  if (n === null) throw Error(P(311));
  n.lastRenderedReducer = e;
  var r = re,
    o = r.baseQueue,
    i = n.pending;
  if (i !== null) {
    if (o !== null) {
      var l = o.next;
      (o.next = i.next), (i.next = l);
    }
    (r.baseQueue = o = i), (n.pending = null);
  }
  if (o !== null) {
    (i = o.next), (r = r.baseState);
    var s = (l = null),
      a = null,
      u = i;
    do {
      var f = u.lane;
      if ((nn & f) === f)
        a !== null &&
          (a = a.next =
            {
              lane: 0,
              action: u.action,
              hasEagerState: u.hasEagerState,
              eagerState: u.eagerState,
              next: null,
            }),
          (r = u.hasEagerState ? u.eagerState : e(r, u.action));
      else {
        var d = {
          lane: f,
          action: u.action,
          hasEagerState: u.hasEagerState,
          eagerState: u.eagerState,
          next: null,
        };
        a === null ? ((s = a = d), (l = r)) : (a = a.next = d),
          (X.lanes |= f),
          (rn |= f);
      }
      u = u.next;
    } while (u !== null && u !== i);
    a === null ? (l = r) : (a.next = s),
      lt(r, t.memoizedState) || (Re = !0),
      (t.memoizedState = r),
      (t.baseState = l),
      (t.baseQueue = a),
      (n.lastRenderedState = r);
  }
  if (((e = n.interleaved), e !== null)) {
    o = e;
    do (i = o.lane), (X.lanes |= i), (rn |= i), (o = o.next);
    while (o !== e);
  } else o === null && (n.lanes = 0);
  return [t.memoizedState, n.dispatch];
}
function bi(e) {
  var t = Ge(),
    n = t.queue;
  if (n === null) throw Error(P(311));
  n.lastRenderedReducer = e;
  var r = n.dispatch,
    o = n.pending,
    i = t.memoizedState;
  if (o !== null) {
    n.pending = null;
    var l = (o = o.next);
    do (i = e(i, l.action)), (l = l.next);
    while (l !== o);
    lt(i, t.memoizedState) || (Re = !0),
      (t.memoizedState = i),
      t.baseQueue === null && (t.baseState = i),
      (n.lastRenderedState = i);
  }
  return [i, r];
}
function Pf() {}
function jf(e, t) {
  var n = X,
    r = Ge(),
    o = t(),
    i = !lt(r.memoizedState, o);
  if (
    (i && ((r.memoizedState = o), (Re = !0)),
    (r = r.queue),
    Ws(zf.bind(null, n, r, e), [e]),
    r.getSnapshot !== t || i || (se !== null && se.memoizedState.tag & 1))
  ) {
    if (
      ((n.flags |= 2048),
      Lr(9, Rf.bind(null, n, r, o, t), void 0, null),
      ae === null)
    )
      throw Error(P(349));
    nn & 30 || Tf(n, t, o);
  }
  return o;
}
function Tf(e, t, n) {
  (e.flags |= 16384),
    (e = { getSnapshot: t, value: n }),
    (t = X.updateQueue),
    t === null
      ? ((t = { lastEffect: null, stores: null }),
        (X.updateQueue = t),
        (t.stores = [e]))
      : ((n = t.stores), n === null ? (t.stores = [e]) : n.push(e));
}
function Rf(e, t, n, r) {
  (t.value = n), (t.getSnapshot = r), Lf(t) && If(e);
}
function zf(e, t, n) {
  return n(function () {
    Lf(t) && If(e);
  });
}
function Lf(e) {
  var t = e.getSnapshot;
  e = e.value;
  try {
    var n = t();
    return !lt(e, n);
  } catch {
    return !0;
  }
}
function If(e) {
  var t = St(e, 1);
  t !== null && ot(t, e, 1, -1);
}
function cu(e) {
  var t = at();
  return (
    typeof e == "function" && (e = e()),
    (t.memoizedState = t.baseState = e),
    (e = {
      pending: null,
      interleaved: null,
      lanes: 0,
      dispatch: null,
      lastRenderedReducer: zr,
      lastRenderedState: e,
    }),
    (t.queue = e),
    (e = e.dispatch = hh.bind(null, X, e)),
    [t.memoizedState, e]
  );
}
function Lr(e, t, n, r) {
  return (
    (e = { tag: e, create: t, destroy: n, deps: r, next: null }),
    (t = X.updateQueue),
    t === null
      ? ((t = { lastEffect: null, stores: null }),
        (X.updateQueue = t),
        (t.lastEffect = e.next = e))
      : ((n = t.lastEffect),
        n === null
          ? (t.lastEffect = e.next = e)
          : ((r = n.next), (n.next = e), (e.next = r), (t.lastEffect = e))),
    e
  );
}
function Of() {
  return Ge().memoizedState;
}
function xo(e, t, n, r) {
  var o = at();
  (X.flags |= e),
    (o.memoizedState = Lr(1 | t, n, void 0, r === void 0 ? null : r));
}
function oi(e, t, n, r) {
  var o = Ge();
  r = r === void 0 ? null : r;
  var i = void 0;
  if (re !== null) {
    var l = re.memoizedState;
    if (((i = l.destroy), r !== null && Vs(r, l.deps))) {
      o.memoizedState = Lr(t, n, i, r);
      return;
    }
  }
  (X.flags |= e), (o.memoizedState = Lr(1 | t, n, i, r));
}
function fu(e, t) {
  return xo(8390656, 8, e, t);
}
function Ws(e, t) {
  return oi(2048, 8, e, t);
}
function Ff(e, t) {
  return oi(4, 2, e, t);
}
function Mf(e, t) {
  return oi(4, 4, e, t);
}
function Df(e, t) {
  if (typeof t == "function")
    return (
      (e = e()),
      t(e),
      function () {
        t(null);
      }
    );
  if (t != null)
    return (
      (e = e()),
      (t.current = e),
      function () {
        t.current = null;
      }
    );
}
function Vf(e, t, n) {
  return (
    (n = n != null ? n.concat([e]) : null), oi(4, 4, Df.bind(null, t, e), n)
  );
}
function Us() {}
function Af(e, t) {
  var n = Ge();
  t = t === void 0 ? null : t;
  var r = n.memoizedState;
  return r !== null && t !== null && Vs(t, r[1])
    ? r[0]
    : ((n.memoizedState = [e, t]), e);
}
function Bf(e, t) {
  var n = Ge();
  t = t === void 0 ? null : t;
  var r = n.memoizedState;
  return r !== null && t !== null && Vs(t, r[1])
    ? r[0]
    : ((e = e()), (n.memoizedState = [e, t]), e);
}
function Wf(e, t, n) {
  return nn & 21
    ? (lt(n, t) || ((n = Qc()), (X.lanes |= n), (rn |= n), (e.baseState = !0)),
      t)
    : (e.baseState && ((e.baseState = !1), (Re = !0)), (e.memoizedState = n));
}
function ph(e, t) {
  var n = A;
  (A = n !== 0 && 4 > n ? n : 4), e(!0);
  var r = Ui.transition;
  Ui.transition = {};
  try {
    e(!1), t();
  } finally {
    (A = n), (Ui.transition = r);
  }
}
function Uf() {
  return Ge().memoizedState;
}
function mh(e, t, n) {
  var r = Vt(e);
  if (
    ((n = {
      lane: r,
      action: n,
      hasEagerState: !1,
      eagerState: null,
      next: null,
    }),
    Hf(e))
  )
    bf(t, n);
  else if (((n = _f(e, t, n, r)), n !== null)) {
    var o = $e();
    ot(n, e, r, o), Qf(n, t, r);
  }
}
function hh(e, t, n) {
  var r = Vt(e),
    o = { lane: r, action: n, hasEagerState: !1, eagerState: null, next: null };
  if (Hf(e)) bf(t, o);
  else {
    var i = e.alternate;
    if (
      e.lanes === 0 &&
      (i === null || i.lanes === 0) &&
      ((i = t.lastRenderedReducer), i !== null)
    )
      try {
        var l = t.lastRenderedState,
          s = i(l, n);
        if (((o.hasEagerState = !0), (o.eagerState = s), lt(s, l))) {
          var a = t.interleaved;
          a === null
            ? ((o.next = o), Is(t))
            : ((o.next = a.next), (a.next = o)),
            (t.interleaved = o);
          return;
        }
      } catch {
      } finally {
      }
    (n = _f(e, t, o, r)),
      n !== null && ((o = $e()), ot(n, e, r, o), Qf(n, t, r));
  }
}
function Hf(e) {
  var t = e.alternate;
  return e === X || (t !== null && t === X);
}
function bf(e, t) {
  mr = Ho = !0;
  var n = e.pending;
  n === null ? (t.next = t) : ((t.next = n.next), (n.next = t)),
    (e.pending = t);
}
function Qf(e, t, n) {
  if (n & 4194240) {
    var r = t.lanes;
    (r &= e.pendingLanes), (n |= r), (t.lanes = n), Ss(e, n);
  }
}
var bo = {
    readContext: Qe,
    useCallback: ve,
    useContext: ve,
    useEffect: ve,
    useImperativeHandle: ve,
    useInsertionEffect: ve,
    useLayoutEffect: ve,
    useMemo: ve,
    useReducer: ve,
    useRef: ve,
    useState: ve,
    useDebugValue: ve,
    useDeferredValue: ve,
    useTransition: ve,
    useMutableSource: ve,
    useSyncExternalStore: ve,
    useId: ve,
    unstable_isNewReconciler: !1,
  },
  yh = {
    readContext: Qe,
    useCallback: function (e, t) {
      return (at().memoizedState = [e, t === void 0 ? null : t]), e;
    },
    useContext: Qe,
    useEffect: fu,
    useImperativeHandle: function (e, t, n) {
      return (
        (n = n != null ? n.concat([e]) : null),
        xo(4194308, 4, Df.bind(null, t, e), n)
      );
    },
    useLayoutEffect: function (e, t) {
      return xo(4194308, 4, e, t);
    },
    useInsertionEffect: function (e, t) {
      return xo(4, 2, e, t);
    },
    useMemo: function (e, t) {
      var n = at();
      return (
        (t = t === void 0 ? null : t), (e = e()), (n.memoizedState = [e, t]), e
      );
    },
    useReducer: function (e, t, n) {
      var r = at();
      return (
        (t = n !== void 0 ? n(t) : t),
        (r.memoizedState = r.baseState = t),
        (e = {
          pending: null,
          interleaved: null,
          lanes: 0,
          dispatch: null,
          lastRenderedReducer: e,
          lastRenderedState: t,
        }),
        (r.queue = e),
        (e = e.dispatch = mh.bind(null, X, e)),
        [r.memoizedState, e]
      );
    },
    useRef: function (e) {
      var t = at();
      return (e = { current: e }), (t.memoizedState = e);
    },
    useState: cu,
    useDebugValue: Us,
    useDeferredValue: function (e) {
      return (at().memoizedState = e);
    },
    useTransition: function () {
      var e = cu(!1),
        t = e[0];
      return (e = ph.bind(null, e[1])), (at().memoizedState = e), [t, e];
    },
    useMutableSource: function () {},
    useSyncExternalStore: function (e, t, n) {
      var r = X,
        o = at();
      if (Y) {
        if (n === void 0) throw Error(P(407));
        n = n();
      } else {
        if (((n = t()), ae === null)) throw Error(P(349));
        nn & 30 || Tf(r, t, n);
      }
      o.memoizedState = n;
      var i = { value: n, getSnapshot: t };
      return (
        (o.queue = i),
        fu(zf.bind(null, r, i, e), [e]),
        (r.flags |= 2048),
        Lr(9, Rf.bind(null, r, i, n, t), void 0, null),
        n
      );
    },
    useId: function () {
      var e = at(),
        t = ae.identifierPrefix;
      if (Y) {
        var n = yt,
          r = ht;
        (n = (r & ~(1 << (32 - rt(r) - 1))).toString(32) + n),
          (t = ":" + t + "R" + n),
          (n = Rr++),
          0 < n && (t += "H" + n.toString(32)),
          (t += ":");
      } else (n = dh++), (t = ":" + t + "r" + n.toString(32) + ":");
      return (e.memoizedState = t);
    },
    unstable_isNewReconciler: !1,
  },
  vh = {
    readContext: Qe,
    useCallback: Af,
    useContext: Qe,
    useEffect: Ws,
    useImperativeHandle: Vf,
    useInsertionEffect: Ff,
    useLayoutEffect: Mf,
    useMemo: Bf,
    useReducer: Hi,
    useRef: Of,
    useState: function () {
      return Hi(zr);
    },
    useDebugValue: Us,
    useDeferredValue: function (e) {
      var t = Ge();
      return Wf(t, re.memoizedState, e);
    },
    useTransition: function () {
      var e = Hi(zr)[0],
        t = Ge().memoizedState;
      return [e, t];
    },
    useMutableSource: Pf,
    useSyncExternalStore: jf,
    useId: Uf,
    unstable_isNewReconciler: !1,
  },
  gh = {
    readContext: Qe,
    useCallback: Af,
    useContext: Qe,
    useEffect: Ws,
    useImperativeHandle: Vf,
    useInsertionEffect: Ff,
    useLayoutEffect: Mf,
    useMemo: Bf,
    useReducer: bi,
    useRef: Of,
    useState: function () {
      return bi(zr);
    },
    useDebugValue: Us,
    useDeferredValue: function (e) {
      var t = Ge();
      return re === null ? (t.memoizedState = e) : Wf(t, re.memoizedState, e);
    },
    useTransition: function () {
      var e = bi(zr)[0],
        t = Ge().memoizedState;
      return [e, t];
    },
    useMutableSource: Pf,
    useSyncExternalStore: jf,
    useId: Uf,
    unstable_isNewReconciler: !1,
  };
function Je(e, t) {
  if (e && e.defaultProps) {
    (t = Z({}, t)), (e = e.defaultProps);
    for (var n in e) t[n] === void 0 && (t[n] = e[n]);
    return t;
  }
  return t;
}
function Il(e, t, n, r) {
  (t = e.memoizedState),
    (n = n(r, t)),
    (n = n == null ? t : Z({}, t, n)),
    (e.memoizedState = n),
    e.lanes === 0 && (e.updateQueue.baseState = n);
}
var ii = {
  isMounted: function (e) {
    return (e = e._reactInternals) ? sn(e) === e : !1;
  },
  enqueueSetState: function (e, t, n) {
    e = e._reactInternals;
    var r = $e(),
      o = Vt(e),
      i = vt(r, o);
    (i.payload = t),
      n != null && (i.callback = n),
      (t = Mt(e, i, o)),
      t !== null && (ot(t, e, o, r), So(t, e, o));
  },
  enqueueReplaceState: function (e, t, n) {
    e = e._reactInternals;
    var r = $e(),
      o = Vt(e),
      i = vt(r, o);
    (i.tag = 1),
      (i.payload = t),
      n != null && (i.callback = n),
      (t = Mt(e, i, o)),
      t !== null && (ot(t, e, o, r), So(t, e, o));
  },
  enqueueForceUpdate: function (e, t) {
    e = e._reactInternals;
    var n = $e(),
      r = Vt(e),
      o = vt(n, r);
    (o.tag = 2),
      t != null && (o.callback = t),
      (t = Mt(e, o, r)),
      t !== null && (ot(t, e, r, n), So(t, e, r));
  },
};
function du(e, t, n, r, o, i, l) {
  return (
    (e = e.stateNode),
    typeof e.shouldComponentUpdate == "function"
      ? e.shouldComponentUpdate(r, i, l)
      : t.prototype && t.prototype.isPureReactComponent
      ? !_r(n, r) || !_r(o, i)
      : !0
  );
}
function Gf(e, t, n) {
  var r = !1,
    o = Wt,
    i = t.contextType;
  return (
    typeof i == "object" && i !== null
      ? (i = Qe(i))
      : ((o = Le(t) ? en : xe.current),
        (r = t.contextTypes),
        (i = (r = r != null) ? On(e, o) : Wt)),
    (t = new t(n, i)),
    (e.memoizedState = t.state !== null && t.state !== void 0 ? t.state : null),
    (t.updater = ii),
    (e.stateNode = t),
    (t._reactInternals = e),
    r &&
      ((e = e.stateNode),
      (e.__reactInternalMemoizedUnmaskedChildContext = o),
      (e.__reactInternalMemoizedMaskedChildContext = i)),
    t
  );
}
function pu(e, t, n, r) {
  (e = t.state),
    typeof t.componentWillReceiveProps == "function" &&
      t.componentWillReceiveProps(n, r),
    typeof t.UNSAFE_componentWillReceiveProps == "function" &&
      t.UNSAFE_componentWillReceiveProps(n, r),
    t.state !== e && ii.enqueueReplaceState(t, t.state, null);
}
function Ol(e, t, n, r) {
  var o = e.stateNode;
  (o.props = n), (o.state = e.memoizedState), (o.refs = {}), Os(e);
  var i = t.contextType;
  typeof i == "object" && i !== null
    ? (o.context = Qe(i))
    : ((i = Le(t) ? en : xe.current), (o.context = On(e, i))),
    (o.state = e.memoizedState),
    (i = t.getDerivedStateFromProps),
    typeof i == "function" && (Il(e, t, i, n), (o.state = e.memoizedState)),
    typeof t.getDerivedStateFromProps == "function" ||
      typeof o.getSnapshotBeforeUpdate == "function" ||
      (typeof o.UNSAFE_componentWillMount != "function" &&
        typeof o.componentWillMount != "function") ||
      ((t = o.state),
      typeof o.componentWillMount == "function" && o.componentWillMount(),
      typeof o.UNSAFE_componentWillMount == "function" &&
        o.UNSAFE_componentWillMount(),
      t !== o.state && ii.enqueueReplaceState(o, o.state, null),
      Wo(e, n, o, r),
      (o.state = e.memoizedState)),
    typeof o.componentDidMount == "function" && (e.flags |= 4194308);
}
function Vn(e, t) {
  try {
    var n = "",
      r = t;
    do (n += Qp(r)), (r = r.return);
    while (r);
    var o = n;
  } catch (i) {
    o =
      `
Error generating stack: ` +
      i.message +
      `
` +
      i.stack;
  }
  return { value: e, source: t, stack: o, digest: null };
}
function Qi(e, t, n) {
  return { value: e, source: null, stack: n ?? null, digest: t ?? null };
}
function Fl(e, t) {
  try {
    console.error(t.value);
  } catch (n) {
    setTimeout(function () {
      throw n;
    });
  }
}
var wh = typeof WeakMap == "function" ? WeakMap : Map;
function Yf(e, t, n) {
  (n = vt(-1, n)), (n.tag = 3), (n.payload = { element: null });
  var r = t.value;
  return (
    (n.callback = function () {
      Go || ((Go = !0), (Ql = r)), Fl(e, t);
    }),
    n
  );
}
function Kf(e, t, n) {
  (n = vt(-1, n)), (n.tag = 3);
  var r = e.type.getDerivedStateFromError;
  if (typeof r == "function") {
    var o = t.value;
    (n.payload = function () {
      return r(o);
    }),
      (n.callback = function () {
        Fl(e, t);
      });
  }
  var i = e.stateNode;
  return (
    i !== null &&
      typeof i.componentDidCatch == "function" &&
      (n.callback = function () {
        Fl(e, t),
          typeof r != "function" &&
            (Dt === null ? (Dt = new Set([this])) : Dt.add(this));
        var l = t.stack;
        this.componentDidCatch(t.value, {
          componentStack: l !== null ? l : "",
        });
      }),
    n
  );
}
function mu(e, t, n) {
  var r = e.pingCache;
  if (r === null) {
    r = e.pingCache = new wh();
    var o = new Set();
    r.set(t, o);
  } else (o = r.get(t)), o === void 0 && ((o = new Set()), r.set(t, o));
  o.has(n) || (o.add(n), (e = Lh.bind(null, e, t, n)), t.then(e, e));
}
function hu(e) {
  do {
    var t;
    if (
      ((t = e.tag === 13) &&
        ((t = e.memoizedState), (t = t !== null ? t.dehydrated !== null : !0)),
      t)
    )
      return e;
    e = e.return;
  } while (e !== null);
  return null;
}
function yu(e, t, n, r, o) {
  return e.mode & 1
    ? ((e.flags |= 65536), (e.lanes = o), e)
    : (e === t
        ? (e.flags |= 65536)
        : ((e.flags |= 128),
          (n.flags |= 131072),
          (n.flags &= -52805),
          n.tag === 1 &&
            (n.alternate === null
              ? (n.tag = 17)
              : ((t = vt(-1, 1)), (t.tag = 2), Mt(n, t, 1))),
          (n.lanes |= 1)),
      e);
}
var Sh = xt.ReactCurrentOwner,
  Re = !1;
function _e(e, t, n, r) {
  t.child = e === null ? Ef(t, null, n, r) : Mn(t, e.child, n, r);
}
function vu(e, t, n, r, o) {
  n = n.render;
  var i = t.ref;
  return (
    Rn(t, o),
    (r = As(e, t, n, r, i, o)),
    (n = Bs()),
    e !== null && !Re
      ? ((t.updateQueue = e.updateQueue),
        (t.flags &= -2053),
        (e.lanes &= ~o),
        kt(e, t, o))
      : (Y && n && Ps(t), (t.flags |= 1), _e(e, t, r, o), t.child)
  );
}
function gu(e, t, n, r, o) {
  if (e === null) {
    var i = n.type;
    return typeof i == "function" &&
      !Zs(i) &&
      i.defaultProps === void 0 &&
      n.compare === null &&
      n.defaultProps === void 0
      ? ((t.tag = 15), (t.type = i), Xf(e, t, i, r, o))
      : ((e = $o(n.type, null, r, t, t.mode, o)),
        (e.ref = t.ref),
        (e.return = t),
        (t.child = e));
  }
  if (((i = e.child), !(e.lanes & o))) {
    var l = i.memoizedProps;
    if (
      ((n = n.compare), (n = n !== null ? n : _r), n(l, r) && e.ref === t.ref)
    )
      return kt(e, t, o);
  }
  return (
    (t.flags |= 1),
    (e = At(i, r)),
    (e.ref = t.ref),
    (e.return = t),
    (t.child = e)
  );
}
function Xf(e, t, n, r, o) {
  if (e !== null) {
    var i = e.memoizedProps;
    if (_r(i, r) && e.ref === t.ref)
      if (((Re = !1), (t.pendingProps = r = i), (e.lanes & o) !== 0))
        e.flags & 131072 && (Re = !0);
      else return (t.lanes = e.lanes), kt(e, t, o);
  }
  return Ml(e, t, n, r, o);
}
function Zf(e, t, n) {
  var r = t.pendingProps,
    o = r.children,
    i = e !== null ? e.memoizedState : null;
  if (r.mode === "hidden")
    if (!(t.mode & 1))
      (t.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }),
        U(_n, Fe),
        (Fe |= n);
    else {
      if (!(n & 1073741824))
        return (
          (e = i !== null ? i.baseLanes | n : n),
          (t.lanes = t.childLanes = 1073741824),
          (t.memoizedState = {
            baseLanes: e,
            cachePool: null,
            transitions: null,
          }),
          (t.updateQueue = null),
          U(_n, Fe),
          (Fe |= e),
          null
        );
      (t.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }),
        (r = i !== null ? i.baseLanes : n),
        U(_n, Fe),
        (Fe |= r);
    }
  else
    i !== null ? ((r = i.baseLanes | n), (t.memoizedState = null)) : (r = n),
      U(_n, Fe),
      (Fe |= r);
  return _e(e, t, o, n), t.child;
}
function Jf(e, t) {
  var n = t.ref;
  ((e === null && n !== null) || (e !== null && e.ref !== n)) &&
    ((t.flags |= 512), (t.flags |= 2097152));
}
function Ml(e, t, n, r, o) {
  var i = Le(n) ? en : xe.current;
  return (
    (i = On(t, i)),
    Rn(t, o),
    (n = As(e, t, n, r, i, o)),
    (r = Bs()),
    e !== null && !Re
      ? ((t.updateQueue = e.updateQueue),
        (t.flags &= -2053),
        (e.lanes &= ~o),
        kt(e, t, o))
      : (Y && r && Ps(t), (t.flags |= 1), _e(e, t, n, o), t.child)
  );
}
function wu(e, t, n, r, o) {
  if (Le(n)) {
    var i = !0;
    Mo(t);
  } else i = !1;
  if ((Rn(t, o), t.stateNode === null))
    Co(e, t), Gf(t, n, r), Ol(t, n, r, o), (r = !0);
  else if (e === null) {
    var l = t.stateNode,
      s = t.memoizedProps;
    l.props = s;
    var a = l.context,
      u = n.contextType;
    typeof u == "object" && u !== null
      ? (u = Qe(u))
      : ((u = Le(n) ? en : xe.current), (u = On(t, u)));
    var f = n.getDerivedStateFromProps,
      d =
        typeof f == "function" ||
        typeof l.getSnapshotBeforeUpdate == "function";
    d ||
      (typeof l.UNSAFE_componentWillReceiveProps != "function" &&
        typeof l.componentWillReceiveProps != "function") ||
      ((s !== r || a !== u) && pu(t, l, r, u)),
      (Pt = !1);
    var h = t.memoizedState;
    (l.state = h),
      Wo(t, r, l, o),
      (a = t.memoizedState),
      s !== r || h !== a || ze.current || Pt
        ? (typeof f == "function" && (Il(t, n, f, r), (a = t.memoizedState)),
          (s = Pt || du(t, n, s, r, h, a, u))
            ? (d ||
                (typeof l.UNSAFE_componentWillMount != "function" &&
                  typeof l.componentWillMount != "function") ||
                (typeof l.componentWillMount == "function" &&
                  l.componentWillMount(),
                typeof l.UNSAFE_componentWillMount == "function" &&
                  l.UNSAFE_componentWillMount()),
              typeof l.componentDidMount == "function" && (t.flags |= 4194308))
            : (typeof l.componentDidMount == "function" && (t.flags |= 4194308),
              (t.memoizedProps = r),
              (t.memoizedState = a)),
          (l.props = r),
          (l.state = a),
          (l.context = u),
          (r = s))
        : (typeof l.componentDidMount == "function" && (t.flags |= 4194308),
          (r = !1));
  } else {
    (l = t.stateNode),
      $f(e, t),
      (s = t.memoizedProps),
      (u = t.type === t.elementType ? s : Je(t.type, s)),
      (l.props = u),
      (d = t.pendingProps),
      (h = l.context),
      (a = n.contextType),
      typeof a == "object" && a !== null
        ? (a = Qe(a))
        : ((a = Le(n) ? en : xe.current), (a = On(t, a)));
    var g = n.getDerivedStateFromProps;
    (f =
      typeof g == "function" ||
      typeof l.getSnapshotBeforeUpdate == "function") ||
      (typeof l.UNSAFE_componentWillReceiveProps != "function" &&
        typeof l.componentWillReceiveProps != "function") ||
      ((s !== d || h !== a) && pu(t, l, r, a)),
      (Pt = !1),
      (h = t.memoizedState),
      (l.state = h),
      Wo(t, r, l, o);
    var y = t.memoizedState;
    s !== d || h !== y || ze.current || Pt
      ? (typeof g == "function" && (Il(t, n, g, r), (y = t.memoizedState)),
        (u = Pt || du(t, n, u, r, h, y, a) || !1)
          ? (f ||
              (typeof l.UNSAFE_componentWillUpdate != "function" &&
                typeof l.componentWillUpdate != "function") ||
              (typeof l.componentWillUpdate == "function" &&
                l.componentWillUpdate(r, y, a),
              typeof l.UNSAFE_componentWillUpdate == "function" &&
                l.UNSAFE_componentWillUpdate(r, y, a)),
            typeof l.componentDidUpdate == "function" && (t.flags |= 4),
            typeof l.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024))
          : (typeof l.componentDidUpdate != "function" ||
              (s === e.memoizedProps && h === e.memoizedState) ||
              (t.flags |= 4),
            typeof l.getSnapshotBeforeUpdate != "function" ||
              (s === e.memoizedProps && h === e.memoizedState) ||
              (t.flags |= 1024),
            (t.memoizedProps = r),
            (t.memoizedState = y)),
        (l.props = r),
        (l.state = y),
        (l.context = a),
        (r = u))
      : (typeof l.componentDidUpdate != "function" ||
          (s === e.memoizedProps && h === e.memoizedState) ||
          (t.flags |= 4),
        typeof l.getSnapshotBeforeUpdate != "function" ||
          (s === e.memoizedProps && h === e.memoizedState) ||
          (t.flags |= 1024),
        (r = !1));
  }
  return Dl(e, t, n, r, i, o);
}
function Dl(e, t, n, r, o, i) {
  Jf(e, t);
  var l = (t.flags & 128) !== 0;
  if (!r && !l) return o && ou(t, n, !1), kt(e, t, i);
  (r = t.stateNode), (Sh.current = t);
  var s =
    l && typeof n.getDerivedStateFromError != "function" ? null : r.render();
  return (
    (t.flags |= 1),
    e !== null && l
      ? ((t.child = Mn(t, e.child, null, i)), (t.child = Mn(t, null, s, i)))
      : _e(e, t, s, i),
    (t.memoizedState = r.state),
    o && ou(t, n, !0),
    t.child
  );
}
function qf(e) {
  var t = e.stateNode;
  t.pendingContext
    ? ru(e, t.pendingContext, t.pendingContext !== t.context)
    : t.context && ru(e, t.context, !1),
    Fs(e, t.containerInfo);
}
function Su(e, t, n, r, o) {
  return Fn(), Ts(o), (t.flags |= 256), _e(e, t, n, r), t.child;
}
var Vl = { dehydrated: null, treeContext: null, retryLane: 0 };
function Al(e) {
  return { baseLanes: e, cachePool: null, transitions: null };
}
function ed(e, t, n) {
  var r = t.pendingProps,
    o = K.current,
    i = !1,
    l = (t.flags & 128) !== 0,
    s;
  if (
    ((s = l) ||
      (s = e !== null && e.memoizedState === null ? !1 : (o & 2) !== 0),
    s
      ? ((i = !0), (t.flags &= -129))
      : (e === null || e.memoizedState !== null) && (o |= 1),
    U(K, o & 1),
    e === null)
  )
    return (
      zl(t),
      (e = t.memoizedState),
      e !== null && ((e = e.dehydrated), e !== null)
        ? (t.mode & 1
            ? e.data === "$!"
              ? (t.lanes = 8)
              : (t.lanes = 1073741824)
            : (t.lanes = 1),
          null)
        : ((l = r.children),
          (e = r.fallback),
          i
            ? ((r = t.mode),
              (i = t.child),
              (l = { mode: "hidden", children: l }),
              !(r & 1) && i !== null
                ? ((i.childLanes = 0), (i.pendingProps = l))
                : (i = ai(l, r, 0, null)),
              (e = qt(e, r, n, null)),
              (i.return = t),
              (e.return = t),
              (i.sibling = e),
              (t.child = i),
              (t.child.memoizedState = Al(n)),
              (t.memoizedState = Vl),
              e)
            : Hs(t, l))
    );
  if (((o = e.memoizedState), o !== null && ((s = o.dehydrated), s !== null)))
    return kh(e, t, l, r, s, o, n);
  if (i) {
    (i = r.fallback), (l = t.mode), (o = e.child), (s = o.sibling);
    var a = { mode: "hidden", children: r.children };
    return (
      !(l & 1) && t.child !== o
        ? ((r = t.child),
          (r.childLanes = 0),
          (r.pendingProps = a),
          (t.deletions = null))
        : ((r = At(o, a)), (r.subtreeFlags = o.subtreeFlags & 14680064)),
      s !== null ? (i = At(s, i)) : ((i = qt(i, l, n, null)), (i.flags |= 2)),
      (i.return = t),
      (r.return = t),
      (r.sibling = i),
      (t.child = r),
      (r = i),
      (i = t.child),
      (l = e.child.memoizedState),
      (l =
        l === null
          ? Al(n)
          : {
              baseLanes: l.baseLanes | n,
              cachePool: null,
              transitions: l.transitions,
            }),
      (i.memoizedState = l),
      (i.childLanes = e.childLanes & ~n),
      (t.memoizedState = Vl),
      r
    );
  }
  return (
    (i = e.child),
    (e = i.sibling),
    (r = At(i, { mode: "visible", children: r.children })),
    !(t.mode & 1) && (r.lanes = n),
    (r.return = t),
    (r.sibling = null),
    e !== null &&
      ((n = t.deletions),
      n === null ? ((t.deletions = [e]), (t.flags |= 16)) : n.push(e)),
    (t.child = r),
    (t.memoizedState = null),
    r
  );
}
function Hs(e, t) {
  return (
    (t = ai({ mode: "visible", children: t }, e.mode, 0, null)),
    (t.return = e),
    (e.child = t)
  );
}
function io(e, t, n, r) {
  return (
    r !== null && Ts(r),
    Mn(t, e.child, null, n),
    (e = Hs(t, t.pendingProps.children)),
    (e.flags |= 2),
    (t.memoizedState = null),
    e
  );
}
function kh(e, t, n, r, o, i, l) {
  if (n)
    return t.flags & 256
      ? ((t.flags &= -257), (r = Qi(Error(P(422)))), io(e, t, l, r))
      : t.memoizedState !== null
      ? ((t.child = e.child), (t.flags |= 128), null)
      : ((i = r.fallback),
        (o = t.mode),
        (r = ai({ mode: "visible", children: r.children }, o, 0, null)),
        (i = qt(i, o, l, null)),
        (i.flags |= 2),
        (r.return = t),
        (i.return = t),
        (r.sibling = i),
        (t.child = r),
        t.mode & 1 && Mn(t, e.child, null, l),
        (t.child.memoizedState = Al(l)),
        (t.memoizedState = Vl),
        i);
  if (!(t.mode & 1)) return io(e, t, l, null);
  if (o.data === "$!") {
    if (((r = o.nextSibling && o.nextSibling.dataset), r)) var s = r.dgst;
    return (r = s), (i = Error(P(419))), (r = Qi(i, r, void 0)), io(e, t, l, r);
  }
  if (((s = (l & e.childLanes) !== 0), Re || s)) {
    if (((r = ae), r !== null)) {
      switch (l & -l) {
        case 4:
          o = 2;
          break;
        case 16:
          o = 8;
          break;
        case 64:
        case 128:
        case 256:
        case 512:
        case 1024:
        case 2048:
        case 4096:
        case 8192:
        case 16384:
        case 32768:
        case 65536:
        case 131072:
        case 262144:
        case 524288:
        case 1048576:
        case 2097152:
        case 4194304:
        case 8388608:
        case 16777216:
        case 33554432:
        case 67108864:
          o = 32;
          break;
        case 536870912:
          o = 268435456;
          break;
        default:
          o = 0;
      }
      (o = o & (r.suspendedLanes | l) ? 0 : o),
        o !== 0 &&
          o !== i.retryLane &&
          ((i.retryLane = o), St(e, o), ot(r, e, o, -1));
    }
    return Xs(), (r = Qi(Error(P(421)))), io(e, t, l, r);
  }
  return o.data === "$?"
    ? ((t.flags |= 128),
      (t.child = e.child),
      (t = Ih.bind(null, e)),
      (o._reactRetry = t),
      null)
    : ((e = i.treeContext),
      (Me = Ft(o.nextSibling)),
      (De = t),
      (Y = !0),
      (et = null),
      e !== null &&
        ((We[Ue++] = ht),
        (We[Ue++] = yt),
        (We[Ue++] = tn),
        (ht = e.id),
        (yt = e.overflow),
        (tn = t)),
      (t = Hs(t, r.children)),
      (t.flags |= 4096),
      t);
}
function ku(e, t, n) {
  e.lanes |= t;
  var r = e.alternate;
  r !== null && (r.lanes |= t), Ll(e.return, t, n);
}
function Gi(e, t, n, r, o) {
  var i = e.memoizedState;
  i === null
    ? (e.memoizedState = {
        isBackwards: t,
        rendering: null,
        renderingStartTime: 0,
        last: r,
        tail: n,
        tailMode: o,
      })
    : ((i.isBackwards = t),
      (i.rendering = null),
      (i.renderingStartTime = 0),
      (i.last = r),
      (i.tail = n),
      (i.tailMode = o));
}
function td(e, t, n) {
  var r = t.pendingProps,
    o = r.revealOrder,
    i = r.tail;
  if ((_e(e, t, r.children, n), (r = K.current), r & 2))
    (r = (r & 1) | 2), (t.flags |= 128);
  else {
    if (e !== null && e.flags & 128)
      e: for (e = t.child; e !== null; ) {
        if (e.tag === 13) e.memoizedState !== null && ku(e, n, t);
        else if (e.tag === 19) ku(e, n, t);
        else if (e.child !== null) {
          (e.child.return = e), (e = e.child);
          continue;
        }
        if (e === t) break e;
        for (; e.sibling === null; ) {
          if (e.return === null || e.return === t) break e;
          e = e.return;
        }
        (e.sibling.return = e.return), (e = e.sibling);
      }
    r &= 1;
  }
  if ((U(K, r), !(t.mode & 1))) t.memoizedState = null;
  else
    switch (o) {
      case "forwards":
        for (n = t.child, o = null; n !== null; )
          (e = n.alternate),
            e !== null && Uo(e) === null && (o = n),
            (n = n.sibling);
        (n = o),
          n === null
            ? ((o = t.child), (t.child = null))
            : ((o = n.sibling), (n.sibling = null)),
          Gi(t, !1, o, n, i);
        break;
      case "backwards":
        for (n = null, o = t.child, t.child = null; o !== null; ) {
          if (((e = o.alternate), e !== null && Uo(e) === null)) {
            t.child = o;
            break;
          }
          (e = o.sibling), (o.sibling = n), (n = o), (o = e);
        }
        Gi(t, !0, n, null, i);
        break;
      case "together":
        Gi(t, !1, null, null, void 0);
        break;
      default:
        t.memoizedState = null;
    }
  return t.child;
}
function Co(e, t) {
  !(t.mode & 1) &&
    e !== null &&
    ((e.alternate = null), (t.alternate = null), (t.flags |= 2));
}
function kt(e, t, n) {
  if (
    (e !== null && (t.dependencies = e.dependencies),
    (rn |= t.lanes),
    !(n & t.childLanes))
  )
    return null;
  if (e !== null && t.child !== e.child) throw Error(P(153));
  if (t.child !== null) {
    for (
      e = t.child, n = At(e, e.pendingProps), t.child = n, n.return = t;
      e.sibling !== null;

    )
      (e = e.sibling), (n = n.sibling = At(e, e.pendingProps)), (n.return = t);
    n.sibling = null;
  }
  return t.child;
}
function xh(e, t, n) {
  switch (t.tag) {
    case 3:
      qf(t), Fn();
      break;
    case 5:
      Nf(t);
      break;
    case 1:
      Le(t.type) && Mo(t);
      break;
    case 4:
      Fs(t, t.stateNode.containerInfo);
      break;
    case 10:
      var r = t.type._context,
        o = t.memoizedProps.value;
      U(Ao, r._currentValue), (r._currentValue = o);
      break;
    case 13:
      if (((r = t.memoizedState), r !== null))
        return r.dehydrated !== null
          ? (U(K, K.current & 1), (t.flags |= 128), null)
          : n & t.child.childLanes
          ? ed(e, t, n)
          : (U(K, K.current & 1),
            (e = kt(e, t, n)),
            e !== null ? e.sibling : null);
      U(K, K.current & 1);
      break;
    case 19:
      if (((r = (n & t.childLanes) !== 0), e.flags & 128)) {
        if (r) return td(e, t, n);
        t.flags |= 128;
      }
      if (
        ((o = t.memoizedState),
        o !== null &&
          ((o.rendering = null), (o.tail = null), (o.lastEffect = null)),
        U(K, K.current),
        r)
      )
        break;
      return null;
    case 22:
    case 23:
      return (t.lanes = 0), Zf(e, t, n);
  }
  return kt(e, t, n);
}
var nd, Bl, rd, od;
nd = function (e, t) {
  for (var n = t.child; n !== null; ) {
    if (n.tag === 5 || n.tag === 6) e.appendChild(n.stateNode);
    else if (n.tag !== 4 && n.child !== null) {
      (n.child.return = n), (n = n.child);
      continue;
    }
    if (n === t) break;
    for (; n.sibling === null; ) {
      if (n.return === null || n.return === t) return;
      n = n.return;
    }
    (n.sibling.return = n.return), (n = n.sibling);
  }
};
Bl = function () {};
rd = function (e, t, n, r) {
  var o = e.memoizedProps;
  if (o !== r) {
    (e = t.stateNode), Zt(ft.current);
    var i = null;
    switch (n) {
      case "input":
        (o = ul(e, o)), (r = ul(e, r)), (i = []);
        break;
      case "select":
        (o = Z({}, o, { value: void 0 })),
          (r = Z({}, r, { value: void 0 })),
          (i = []);
        break;
      case "textarea":
        (o = dl(e, o)), (r = dl(e, r)), (i = []);
        break;
      default:
        typeof o.onClick != "function" &&
          typeof r.onClick == "function" &&
          (e.onclick = Oo);
    }
    ml(n, r);
    var l;
    n = null;
    for (u in o)
      if (!r.hasOwnProperty(u) && o.hasOwnProperty(u) && o[u] != null)
        if (u === "style") {
          var s = o[u];
          for (l in s) s.hasOwnProperty(l) && (n || (n = {}), (n[l] = ""));
        } else
          u !== "dangerouslySetInnerHTML" &&
            u !== "children" &&
            u !== "suppressContentEditableWarning" &&
            u !== "suppressHydrationWarning" &&
            u !== "autoFocus" &&
            (gr.hasOwnProperty(u)
              ? i || (i = [])
              : (i = i || []).push(u, null));
    for (u in r) {
      var a = r[u];
      if (
        ((s = o != null ? o[u] : void 0),
        r.hasOwnProperty(u) && a !== s && (a != null || s != null))
      )
        if (u === "style")
          if (s) {
            for (l in s)
              !s.hasOwnProperty(l) ||
                (a && a.hasOwnProperty(l)) ||
                (n || (n = {}), (n[l] = ""));
            for (l in a)
              a.hasOwnProperty(l) &&
                s[l] !== a[l] &&
                (n || (n = {}), (n[l] = a[l]));
          } else n || (i || (i = []), i.push(u, n)), (n = a);
        else
          u === "dangerouslySetInnerHTML"
            ? ((a = a ? a.__html : void 0),
              (s = s ? s.__html : void 0),
              a != null && s !== a && (i = i || []).push(u, a))
            : u === "children"
            ? (typeof a != "string" && typeof a != "number") ||
              (i = i || []).push(u, "" + a)
            : u !== "suppressContentEditableWarning" &&
              u !== "suppressHydrationWarning" &&
              (gr.hasOwnProperty(u)
                ? (a != null && u === "onScroll" && Q("scroll", e),
                  i || s === a || (i = []))
                : (i = i || []).push(u, a));
    }
    n && (i = i || []).push("style", n);
    var u = i;
    (t.updateQueue = u) && (t.flags |= 4);
  }
};
od = function (e, t, n, r) {
  n !== r && (t.flags |= 4);
};
function Jn(e, t) {
  if (!Y)
    switch (e.tailMode) {
      case "hidden":
        t = e.tail;
        for (var n = null; t !== null; )
          t.alternate !== null && (n = t), (t = t.sibling);
        n === null ? (e.tail = null) : (n.sibling = null);
        break;
      case "collapsed":
        n = e.tail;
        for (var r = null; n !== null; )
          n.alternate !== null && (r = n), (n = n.sibling);
        r === null
          ? t || e.tail === null
            ? (e.tail = null)
            : (e.tail.sibling = null)
          : (r.sibling = null);
    }
}
function ge(e) {
  var t = e.alternate !== null && e.alternate.child === e.child,
    n = 0,
    r = 0;
  if (t)
    for (var o = e.child; o !== null; )
      (n |= o.lanes | o.childLanes),
        (r |= o.subtreeFlags & 14680064),
        (r |= o.flags & 14680064),
        (o.return = e),
        (o = o.sibling);
  else
    for (o = e.child; o !== null; )
      (n |= o.lanes | o.childLanes),
        (r |= o.subtreeFlags),
        (r |= o.flags),
        (o.return = e),
        (o = o.sibling);
  return (e.subtreeFlags |= r), (e.childLanes = n), t;
}
function Ch(e, t, n) {
  var r = t.pendingProps;
  switch ((js(t), t.tag)) {
    case 2:
    case 16:
    case 15:
    case 0:
    case 11:
    case 7:
    case 8:
    case 12:
    case 9:
    case 14:
      return ge(t), null;
    case 1:
      return Le(t.type) && Fo(), ge(t), null;
    case 3:
      return (
        (r = t.stateNode),
        Dn(),
        G(ze),
        G(xe),
        Ds(),
        r.pendingContext &&
          ((r.context = r.pendingContext), (r.pendingContext = null)),
        (e === null || e.child === null) &&
          (ro(t)
            ? (t.flags |= 4)
            : e === null ||
              (e.memoizedState.isDehydrated && !(t.flags & 256)) ||
              ((t.flags |= 1024), et !== null && (Kl(et), (et = null)))),
        Bl(e, t),
        ge(t),
        null
      );
    case 5:
      Ms(t);
      var o = Zt(Tr.current);
      if (((n = t.type), e !== null && t.stateNode != null))
        rd(e, t, n, r, o),
          e.ref !== t.ref && ((t.flags |= 512), (t.flags |= 2097152));
      else {
        if (!r) {
          if (t.stateNode === null) throw Error(P(166));
          return ge(t), null;
        }
        if (((e = Zt(ft.current)), ro(t))) {
          (r = t.stateNode), (n = t.type);
          var i = t.memoizedProps;
          switch (((r[ut] = t), (r[Pr] = i), (e = (t.mode & 1) !== 0), n)) {
            case "dialog":
              Q("cancel", r), Q("close", r);
              break;
            case "iframe":
            case "object":
            case "embed":
              Q("load", r);
              break;
            case "video":
            case "audio":
              for (o = 0; o < sr.length; o++) Q(sr[o], r);
              break;
            case "source":
              Q("error", r);
              break;
            case "img":
            case "image":
            case "link":
              Q("error", r), Q("load", r);
              break;
            case "details":
              Q("toggle", r);
              break;
            case "input":
              Ta(r, i), Q("invalid", r);
              break;
            case "select":
              (r._wrapperState = { wasMultiple: !!i.multiple }),
                Q("invalid", r);
              break;
            case "textarea":
              za(r, i), Q("invalid", r);
          }
          ml(n, i), (o = null);
          for (var l in i)
            if (i.hasOwnProperty(l)) {
              var s = i[l];
              l === "children"
                ? typeof s == "string"
                  ? r.textContent !== s &&
                    (i.suppressHydrationWarning !== !0 &&
                      no(r.textContent, s, e),
                    (o = ["children", s]))
                  : typeof s == "number" &&
                    r.textContent !== "" + s &&
                    (i.suppressHydrationWarning !== !0 &&
                      no(r.textContent, s, e),
                    (o = ["children", "" + s]))
                : gr.hasOwnProperty(l) &&
                  s != null &&
                  l === "onScroll" &&
                  Q("scroll", r);
            }
          switch (n) {
            case "input":
              Yr(r), Ra(r, i, !0);
              break;
            case "textarea":
              Yr(r), La(r);
              break;
            case "select":
            case "option":
              break;
            default:
              typeof i.onClick == "function" && (r.onclick = Oo);
          }
          (r = o), (t.updateQueue = r), r !== null && (t.flags |= 4);
        } else {
          (l = o.nodeType === 9 ? o : o.ownerDocument),
            e === "http://www.w3.org/1999/xhtml" && (e = Rc(n)),
            e === "http://www.w3.org/1999/xhtml"
              ? n === "script"
                ? ((e = l.createElement("div")),
                  (e.innerHTML = "<script></script>"),
                  (e = e.removeChild(e.firstChild)))
                : typeof r.is == "string"
                ? (e = l.createElement(n, { is: r.is }))
                : ((e = l.createElement(n)),
                  n === "select" &&
                    ((l = e),
                    r.multiple
                      ? (l.multiple = !0)
                      : r.size && (l.size = r.size)))
              : (e = l.createElementNS(e, n)),
            (e[ut] = t),
            (e[Pr] = r),
            nd(e, t, !1, !1),
            (t.stateNode = e);
          e: {
            switch (((l = hl(n, r)), n)) {
              case "dialog":
                Q("cancel", e), Q("close", e), (o = r);
                break;
              case "iframe":
              case "object":
              case "embed":
                Q("load", e), (o = r);
                break;
              case "video":
              case "audio":
                for (o = 0; o < sr.length; o++) Q(sr[o], e);
                o = r;
                break;
              case "source":
                Q("error", e), (o = r);
                break;
              case "img":
              case "image":
              case "link":
                Q("error", e), Q("load", e), (o = r);
                break;
              case "details":
                Q("toggle", e), (o = r);
                break;
              case "input":
                Ta(e, r), (o = ul(e, r)), Q("invalid", e);
                break;
              case "option":
                o = r;
                break;
              case "select":
                (e._wrapperState = { wasMultiple: !!r.multiple }),
                  (o = Z({}, r, { value: void 0 })),
                  Q("invalid", e);
                break;
              case "textarea":
                za(e, r), (o = dl(e, r)), Q("invalid", e);
                break;
              default:
                o = r;
            }
            ml(n, o), (s = o);
            for (i in s)
              if (s.hasOwnProperty(i)) {
                var a = s[i];
                i === "style"
                  ? Ic(e, a)
                  : i === "dangerouslySetInnerHTML"
                  ? ((a = a ? a.__html : void 0), a != null && zc(e, a))
                  : i === "children"
                  ? typeof a == "string"
                    ? (n !== "textarea" || a !== "") && wr(e, a)
                    : typeof a == "number" && wr(e, "" + a)
                  : i !== "suppressContentEditableWarning" &&
                    i !== "suppressHydrationWarning" &&
                    i !== "autoFocus" &&
                    (gr.hasOwnProperty(i)
                      ? a != null && i === "onScroll" && Q("scroll", e)
                      : a != null && ms(e, i, a, l));
              }
            switch (n) {
              case "input":
                Yr(e), Ra(e, r, !1);
                break;
              case "textarea":
                Yr(e), La(e);
                break;
              case "option":
                r.value != null && e.setAttribute("value", "" + Bt(r.value));
                break;
              case "select":
                (e.multiple = !!r.multiple),
                  (i = r.value),
                  i != null
                    ? Nn(e, !!r.multiple, i, !1)
                    : r.defaultValue != null &&
                      Nn(e, !!r.multiple, r.defaultValue, !0);
                break;
              default:
                typeof o.onClick == "function" && (e.onclick = Oo);
            }
            switch (n) {
              case "button":
              case "input":
              case "select":
              case "textarea":
                r = !!r.autoFocus;
                break e;
              case "img":
                r = !0;
                break e;
              default:
                r = !1;
            }
          }
          r && (t.flags |= 4);
        }
        t.ref !== null && ((t.flags |= 512), (t.flags |= 2097152));
      }
      return ge(t), null;
    case 6:
      if (e && t.stateNode != null) od(e, t, e.memoizedProps, r);
      else {
        if (typeof r != "string" && t.stateNode === null) throw Error(P(166));
        if (((n = Zt(Tr.current)), Zt(ft.current), ro(t))) {
          if (
            ((r = t.stateNode),
            (n = t.memoizedProps),
            (r[ut] = t),
            (i = r.nodeValue !== n) && ((e = De), e !== null))
          )
            switch (e.tag) {
              case 3:
                no(r.nodeValue, n, (e.mode & 1) !== 0);
                break;
              case 5:
                e.memoizedProps.suppressHydrationWarning !== !0 &&
                  no(r.nodeValue, n, (e.mode & 1) !== 0);
            }
          i && (t.flags |= 4);
        } else
          (r = (n.nodeType === 9 ? n : n.ownerDocument).createTextNode(r)),
            (r[ut] = t),
            (t.stateNode = r);
      }
      return ge(t), null;
    case 13:
      if (
        (G(K),
        (r = t.memoizedState),
        e === null ||
          (e.memoizedState !== null && e.memoizedState.dehydrated !== null))
      ) {
        if (Y && Me !== null && t.mode & 1 && !(t.flags & 128))
          xf(), Fn(), (t.flags |= 98560), (i = !1);
        else if (((i = ro(t)), r !== null && r.dehydrated !== null)) {
          if (e === null) {
            if (!i) throw Error(P(318));
            if (
              ((i = t.memoizedState),
              (i = i !== null ? i.dehydrated : null),
              !i)
            )
              throw Error(P(317));
            i[ut] = t;
          } else
            Fn(), !(t.flags & 128) && (t.memoizedState = null), (t.flags |= 4);
          ge(t), (i = !1);
        } else et !== null && (Kl(et), (et = null)), (i = !0);
        if (!i) return t.flags & 65536 ? t : null;
      }
      return t.flags & 128
        ? ((t.lanes = n), t)
        : ((r = r !== null),
          r !== (e !== null && e.memoizedState !== null) &&
            r &&
            ((t.child.flags |= 8192),
            t.mode & 1 &&
              (e === null || K.current & 1 ? oe === 0 && (oe = 3) : Xs())),
          t.updateQueue !== null && (t.flags |= 4),
          ge(t),
          null);
    case 4:
      return (
        Dn(), Bl(e, t), e === null && $r(t.stateNode.containerInfo), ge(t), null
      );
    case 10:
      return Ls(t.type._context), ge(t), null;
    case 17:
      return Le(t.type) && Fo(), ge(t), null;
    case 19:
      if ((G(K), (i = t.memoizedState), i === null)) return ge(t), null;
      if (((r = (t.flags & 128) !== 0), (l = i.rendering), l === null))
        if (r) Jn(i, !1);
        else {
          if (oe !== 0 || (e !== null && e.flags & 128))
            for (e = t.child; e !== null; ) {
              if (((l = Uo(e)), l !== null)) {
                for (
                  t.flags |= 128,
                    Jn(i, !1),
                    r = l.updateQueue,
                    r !== null && ((t.updateQueue = r), (t.flags |= 4)),
                    t.subtreeFlags = 0,
                    r = n,
                    n = t.child;
                  n !== null;

                )
                  (i = n),
                    (e = r),
                    (i.flags &= 14680066),
                    (l = i.alternate),
                    l === null
                      ? ((i.childLanes = 0),
                        (i.lanes = e),
                        (i.child = null),
                        (i.subtreeFlags = 0),
                        (i.memoizedProps = null),
                        (i.memoizedState = null),
                        (i.updateQueue = null),
                        (i.dependencies = null),
                        (i.stateNode = null))
                      : ((i.childLanes = l.childLanes),
                        (i.lanes = l.lanes),
                        (i.child = l.child),
                        (i.subtreeFlags = 0),
                        (i.deletions = null),
                        (i.memoizedProps = l.memoizedProps),
                        (i.memoizedState = l.memoizedState),
                        (i.updateQueue = l.updateQueue),
                        (i.type = l.type),
                        (e = l.dependencies),
                        (i.dependencies =
                          e === null
                            ? null
                            : {
                                lanes: e.lanes,
                                firstContext: e.firstContext,
                              })),
                    (n = n.sibling);
                return U(K, (K.current & 1) | 2), t.child;
              }
              e = e.sibling;
            }
          i.tail !== null &&
            ee() > An &&
            ((t.flags |= 128), (r = !0), Jn(i, !1), (t.lanes = 4194304));
        }
      else {
        if (!r)
          if (((e = Uo(l)), e !== null)) {
            if (
              ((t.flags |= 128),
              (r = !0),
              (n = e.updateQueue),
              n !== null && ((t.updateQueue = n), (t.flags |= 4)),
              Jn(i, !0),
              i.tail === null && i.tailMode === "hidden" && !l.alternate && !Y)
            )
              return ge(t), null;
          } else
            2 * ee() - i.renderingStartTime > An &&
              n !== 1073741824 &&
              ((t.flags |= 128), (r = !0), Jn(i, !1), (t.lanes = 4194304));
        i.isBackwards
          ? ((l.sibling = t.child), (t.child = l))
          : ((n = i.last),
            n !== null ? (n.sibling = l) : (t.child = l),
            (i.last = l));
      }
      return i.tail !== null
        ? ((t = i.tail),
          (i.rendering = t),
          (i.tail = t.sibling),
          (i.renderingStartTime = ee()),
          (t.sibling = null),
          (n = K.current),
          U(K, r ? (n & 1) | 2 : n & 1),
          t)
        : (ge(t), null);
    case 22:
    case 23:
      return (
        Ks(),
        (r = t.memoizedState !== null),
        e !== null && (e.memoizedState !== null) !== r && (t.flags |= 8192),
        r && t.mode & 1
          ? Fe & 1073741824 && (ge(t), t.subtreeFlags & 6 && (t.flags |= 8192))
          : ge(t),
        null
      );
    case 24:
      return null;
    case 25:
      return null;
  }
  throw Error(P(156, t.tag));
}
function Eh(e, t) {
  switch ((js(t), t.tag)) {
    case 1:
      return (
        Le(t.type) && Fo(),
        (e = t.flags),
        e & 65536 ? ((t.flags = (e & -65537) | 128), t) : null
      );
    case 3:
      return (
        Dn(),
        G(ze),
        G(xe),
        Ds(),
        (e = t.flags),
        e & 65536 && !(e & 128) ? ((t.flags = (e & -65537) | 128), t) : null
      );
    case 5:
      return Ms(t), null;
    case 13:
      if ((G(K), (e = t.memoizedState), e !== null && e.dehydrated !== null)) {
        if (t.alternate === null) throw Error(P(340));
        Fn();
      }
      return (
        (e = t.flags), e & 65536 ? ((t.flags = (e & -65537) | 128), t) : null
      );
    case 19:
      return G(K), null;
    case 4:
      return Dn(), null;
    case 10:
      return Ls(t.type._context), null;
    case 22:
    case 23:
      return Ks(), null;
    case 24:
      return null;
    default:
      return null;
  }
}
var lo = !1,
  we = !1,
  _h = typeof WeakSet == "function" ? WeakSet : Set,
  R = null;
function En(e, t) {
  var n = e.ref;
  if (n !== null)
    if (typeof n == "function")
      try {
        n(null);
      } catch (r) {
        q(e, t, r);
      }
    else n.current = null;
}
function Wl(e, t, n) {
  try {
    n();
  } catch (r) {
    q(e, t, r);
  }
}
var xu = !1;
function $h(e, t) {
  if (((_l = zo), (e = uf()), Ns(e))) {
    if ("selectionStart" in e)
      var n = { start: e.selectionStart, end: e.selectionEnd };
    else
      e: {
        n = ((n = e.ownerDocument) && n.defaultView) || window;
        var r = n.getSelection && n.getSelection();
        if (r && r.rangeCount !== 0) {
          n = r.anchorNode;
          var o = r.anchorOffset,
            i = r.focusNode;
          r = r.focusOffset;
          try {
            n.nodeType, i.nodeType;
          } catch {
            n = null;
            break e;
          }
          var l = 0,
            s = -1,
            a = -1,
            u = 0,
            f = 0,
            d = e,
            h = null;
          t: for (;;) {
            for (
              var g;
              d !== n || (o !== 0 && d.nodeType !== 3) || (s = l + o),
                d !== i || (r !== 0 && d.nodeType !== 3) || (a = l + r),
                d.nodeType === 3 && (l += d.nodeValue.length),
                (g = d.firstChild) !== null;

            )
              (h = d), (d = g);
            for (;;) {
              if (d === e) break t;
              if (
                (h === n && ++u === o && (s = l),
                h === i && ++f === r && (a = l),
                (g = d.nextSibling) !== null)
              )
                break;
              (d = h), (h = d.parentNode);
            }
            d = g;
          }
          n = s === -1 || a === -1 ? null : { start: s, end: a };
        } else n = null;
      }
    n = n || { start: 0, end: 0 };
  } else n = null;
  for ($l = { focusedElem: e, selectionRange: n }, zo = !1, R = t; R !== null; )
    if (((t = R), (e = t.child), (t.subtreeFlags & 1028) !== 0 && e !== null))
      (e.return = t), (R = e);
    else
      for (; R !== null; ) {
        t = R;
        try {
          var y = t.alternate;
          if (t.flags & 1024)
            switch (t.tag) {
              case 0:
              case 11:
              case 15:
                break;
              case 1:
                if (y !== null) {
                  var v = y.memoizedProps,
                    C = y.memoizedState,
                    m = t.stateNode,
                    c = m.getSnapshotBeforeUpdate(
                      t.elementType === t.type ? v : Je(t.type, v),
                      C
                    );
                  m.__reactInternalSnapshotBeforeUpdate = c;
                }
                break;
              case 3:
                var p = t.stateNode.containerInfo;
                p.nodeType === 1
                  ? (p.textContent = "")
                  : p.nodeType === 9 &&
                    p.documentElement &&
                    p.removeChild(p.documentElement);
                break;
              case 5:
              case 6:
              case 4:
              case 17:
                break;
              default:
                throw Error(P(163));
            }
        } catch (S) {
          q(t, t.return, S);
        }
        if (((e = t.sibling), e !== null)) {
          (e.return = t.return), (R = e);
          break;
        }
        R = t.return;
      }
  return (y = xu), (xu = !1), y;
}
function hr(e, t, n) {
  var r = t.updateQueue;
  if (((r = r !== null ? r.lastEffect : null), r !== null)) {
    var o = (r = r.next);
    do {
      if ((o.tag & e) === e) {
        var i = o.destroy;
        (o.destroy = void 0), i !== void 0 && Wl(t, n, i);
      }
      o = o.next;
    } while (o !== r);
  }
}
function li(e, t) {
  if (
    ((t = t.updateQueue), (t = t !== null ? t.lastEffect : null), t !== null)
  ) {
    var n = (t = t.next);
    do {
      if ((n.tag & e) === e) {
        var r = n.create;
        n.destroy = r();
      }
      n = n.next;
    } while (n !== t);
  }
}
function Ul(e) {
  var t = e.ref;
  if (t !== null) {
    var n = e.stateNode;
    switch (e.tag) {
      case 5:
        e = n;
        break;
      default:
        e = n;
    }
    typeof t == "function" ? t(e) : (t.current = e);
  }
}
function id(e) {
  var t = e.alternate;
  t !== null && ((e.alternate = null), id(t)),
    (e.child = null),
    (e.deletions = null),
    (e.sibling = null),
    e.tag === 5 &&
      ((t = e.stateNode),
      t !== null &&
        (delete t[ut], delete t[Pr], delete t[jl], delete t[ah], delete t[uh])),
    (e.stateNode = null),
    (e.return = null),
    (e.dependencies = null),
    (e.memoizedProps = null),
    (e.memoizedState = null),
    (e.pendingProps = null),
    (e.stateNode = null),
    (e.updateQueue = null);
}
function ld(e) {
  return e.tag === 5 || e.tag === 3 || e.tag === 4;
}
function Cu(e) {
  e: for (;;) {
    for (; e.sibling === null; ) {
      if (e.return === null || ld(e.return)) return null;
      e = e.return;
    }
    for (
      e.sibling.return = e.return, e = e.sibling;
      e.tag !== 5 && e.tag !== 6 && e.tag !== 18;

    ) {
      if (e.flags & 2 || e.child === null || e.tag === 4) continue e;
      (e.child.return = e), (e = e.child);
    }
    if (!(e.flags & 2)) return e.stateNode;
  }
}
function Hl(e, t, n) {
  var r = e.tag;
  if (r === 5 || r === 6)
    (e = e.stateNode),
      t
        ? n.nodeType === 8
          ? n.parentNode.insertBefore(e, t)
          : n.insertBefore(e, t)
        : (n.nodeType === 8
            ? ((t = n.parentNode), t.insertBefore(e, n))
            : ((t = n), t.appendChild(e)),
          (n = n._reactRootContainer),
          n != null || t.onclick !== null || (t.onclick = Oo));
  else if (r !== 4 && ((e = e.child), e !== null))
    for (Hl(e, t, n), e = e.sibling; e !== null; ) Hl(e, t, n), (e = e.sibling);
}
function bl(e, t, n) {
  var r = e.tag;
  if (r === 5 || r === 6)
    (e = e.stateNode), t ? n.insertBefore(e, t) : n.appendChild(e);
  else if (r !== 4 && ((e = e.child), e !== null))
    for (bl(e, t, n), e = e.sibling; e !== null; ) bl(e, t, n), (e = e.sibling);
}
var pe = null,
  qe = !1;
function $t(e, t, n) {
  for (n = n.child; n !== null; ) sd(e, t, n), (n = n.sibling);
}
function sd(e, t, n) {
  if (ct && typeof ct.onCommitFiberUnmount == "function")
    try {
      ct.onCommitFiberUnmount(Jo, n);
    } catch {}
  switch (n.tag) {
    case 5:
      we || En(n, t);
    case 6:
      var r = pe,
        o = qe;
      (pe = null),
        $t(e, t, n),
        (pe = r),
        (qe = o),
        pe !== null &&
          (qe
            ? ((e = pe),
              (n = n.stateNode),
              e.nodeType === 8 ? e.parentNode.removeChild(n) : e.removeChild(n))
            : pe.removeChild(n.stateNode));
      break;
    case 18:
      pe !== null &&
        (qe
          ? ((e = pe),
            (n = n.stateNode),
            e.nodeType === 8
              ? Ai(e.parentNode, n)
              : e.nodeType === 1 && Ai(e, n),
            Cr(e))
          : Ai(pe, n.stateNode));
      break;
    case 4:
      (r = pe),
        (o = qe),
        (pe = n.stateNode.containerInfo),
        (qe = !0),
        $t(e, t, n),
        (pe = r),
        (qe = o);
      break;
    case 0:
    case 11:
    case 14:
    case 15:
      if (
        !we &&
        ((r = n.updateQueue), r !== null && ((r = r.lastEffect), r !== null))
      ) {
        o = r = r.next;
        do {
          var i = o,
            l = i.destroy;
          (i = i.tag),
            l !== void 0 && (i & 2 || i & 4) && Wl(n, t, l),
            (o = o.next);
        } while (o !== r);
      }
      $t(e, t, n);
      break;
    case 1:
      if (
        !we &&
        (En(n, t),
        (r = n.stateNode),
        typeof r.componentWillUnmount == "function")
      )
        try {
          (r.props = n.memoizedProps),
            (r.state = n.memoizedState),
            r.componentWillUnmount();
        } catch (s) {
          q(n, t, s);
        }
      $t(e, t, n);
      break;
    case 21:
      $t(e, t, n);
      break;
    case 22:
      n.mode & 1
        ? ((we = (r = we) || n.memoizedState !== null), $t(e, t, n), (we = r))
        : $t(e, t, n);
      break;
    default:
      $t(e, t, n);
  }
}
function Eu(e) {
  var t = e.updateQueue;
  if (t !== null) {
    e.updateQueue = null;
    var n = e.stateNode;
    n === null && (n = e.stateNode = new _h()),
      t.forEach(function (r) {
        var o = Oh.bind(null, e, r);
        n.has(r) || (n.add(r), r.then(o, o));
      });
  }
}
function Ze(e, t) {
  var n = t.deletions;
  if (n !== null)
    for (var r = 0; r < n.length; r++) {
      var o = n[r];
      try {
        var i = e,
          l = t,
          s = l;
        e: for (; s !== null; ) {
          switch (s.tag) {
            case 5:
              (pe = s.stateNode), (qe = !1);
              break e;
            case 3:
              (pe = s.stateNode.containerInfo), (qe = !0);
              break e;
            case 4:
              (pe = s.stateNode.containerInfo), (qe = !0);
              break e;
          }
          s = s.return;
        }
        if (pe === null) throw Error(P(160));
        sd(i, l, o), (pe = null), (qe = !1);
        var a = o.alternate;
        a !== null && (a.return = null), (o.return = null);
      } catch (u) {
        q(o, t, u);
      }
    }
  if (t.subtreeFlags & 12854)
    for (t = t.child; t !== null; ) ad(t, e), (t = t.sibling);
}
function ad(e, t) {
  var n = e.alternate,
    r = e.flags;
  switch (e.tag) {
    case 0:
    case 11:
    case 14:
    case 15:
      if ((Ze(t, e), st(e), r & 4)) {
        try {
          hr(3, e, e.return), li(3, e);
        } catch (v) {
          q(e, e.return, v);
        }
        try {
          hr(5, e, e.return);
        } catch (v) {
          q(e, e.return, v);
        }
      }
      break;
    case 1:
      Ze(t, e), st(e), r & 512 && n !== null && En(n, n.return);
      break;
    case 5:
      if (
        (Ze(t, e),
        st(e),
        r & 512 && n !== null && En(n, n.return),
        e.flags & 32)
      ) {
        var o = e.stateNode;
        try {
          wr(o, "");
        } catch (v) {
          q(e, e.return, v);
        }
      }
      if (r & 4 && ((o = e.stateNode), o != null)) {
        var i = e.memoizedProps,
          l = n !== null ? n.memoizedProps : i,
          s = e.type,
          a = e.updateQueue;
        if (((e.updateQueue = null), a !== null))
          try {
            s === "input" && i.type === "radio" && i.name != null && jc(o, i),
              hl(s, l);
            var u = hl(s, i);
            for (l = 0; l < a.length; l += 2) {
              var f = a[l],
                d = a[l + 1];
              f === "style"
                ? Ic(o, d)
                : f === "dangerouslySetInnerHTML"
                ? zc(o, d)
                : f === "children"
                ? wr(o, d)
                : ms(o, f, d, u);
            }
            switch (s) {
              case "input":
                cl(o, i);
                break;
              case "textarea":
                Tc(o, i);
                break;
              case "select":
                var h = o._wrapperState.wasMultiple;
                o._wrapperState.wasMultiple = !!i.multiple;
                var g = i.value;
                g != null
                  ? Nn(o, !!i.multiple, g, !1)
                  : h !== !!i.multiple &&
                    (i.defaultValue != null
                      ? Nn(o, !!i.multiple, i.defaultValue, !0)
                      : Nn(o, !!i.multiple, i.multiple ? [] : "", !1));
            }
            o[Pr] = i;
          } catch (v) {
            q(e, e.return, v);
          }
      }
      break;
    case 6:
      if ((Ze(t, e), st(e), r & 4)) {
        if (e.stateNode === null) throw Error(P(162));
        (o = e.stateNode), (i = e.memoizedProps);
        try {
          o.nodeValue = i;
        } catch (v) {
          q(e, e.return, v);
        }
      }
      break;
    case 3:
      if (
        (Ze(t, e), st(e), r & 4 && n !== null && n.memoizedState.isDehydrated)
      )
        try {
          Cr(t.containerInfo);
        } catch (v) {
          q(e, e.return, v);
        }
      break;
    case 4:
      Ze(t, e), st(e);
      break;
    case 13:
      Ze(t, e),
        st(e),
        (o = e.child),
        o.flags & 8192 &&
          ((i = o.memoizedState !== null),
          (o.stateNode.isHidden = i),
          !i ||
            (o.alternate !== null && o.alternate.memoizedState !== null) ||
            (Gs = ee())),
        r & 4 && Eu(e);
      break;
    case 22:
      if (
        ((f = n !== null && n.memoizedState !== null),
        e.mode & 1 ? ((we = (u = we) || f), Ze(t, e), (we = u)) : Ze(t, e),
        st(e),
        r & 8192)
      ) {
        if (
          ((u = e.memoizedState !== null),
          (e.stateNode.isHidden = u) && !f && e.mode & 1)
        )
          for (R = e, f = e.child; f !== null; ) {
            for (d = R = f; R !== null; ) {
              switch (((h = R), (g = h.child), h.tag)) {
                case 0:
                case 11:
                case 14:
                case 15:
                  hr(4, h, h.return);
                  break;
                case 1:
                  En(h, h.return);
                  var y = h.stateNode;
                  if (typeof y.componentWillUnmount == "function") {
                    (r = h), (n = h.return);
                    try {
                      (t = r),
                        (y.props = t.memoizedProps),
                        (y.state = t.memoizedState),
                        y.componentWillUnmount();
                    } catch (v) {
                      q(r, n, v);
                    }
                  }
                  break;
                case 5:
                  En(h, h.return);
                  break;
                case 22:
                  if (h.memoizedState !== null) {
                    $u(d);
                    continue;
                  }
              }
              g !== null ? ((g.return = h), (R = g)) : $u(d);
            }
            f = f.sibling;
          }
        e: for (f = null, d = e; ; ) {
          if (d.tag === 5) {
            if (f === null) {
              f = d;
              try {
                (o = d.stateNode),
                  u
                    ? ((i = o.style),
                      typeof i.setProperty == "function"
                        ? i.setProperty("display", "none", "important")
                        : (i.display = "none"))
                    : ((s = d.stateNode),
                      (a = d.memoizedProps.style),
                      (l =
                        a != null && a.hasOwnProperty("display")
                          ? a.display
                          : null),
                      (s.style.display = Lc("display", l)));
              } catch (v) {
                q(e, e.return, v);
              }
            }
          } else if (d.tag === 6) {
            if (f === null)
              try {
                d.stateNode.nodeValue = u ? "" : d.memoizedProps;
              } catch (v) {
                q(e, e.return, v);
              }
          } else if (
            ((d.tag !== 22 && d.tag !== 23) ||
              d.memoizedState === null ||
              d === e) &&
            d.child !== null
          ) {
            (d.child.return = d), (d = d.child);
            continue;
          }
          if (d === e) break e;
          for (; d.sibling === null; ) {
            if (d.return === null || d.return === e) break e;
            f === d && (f = null), (d = d.return);
          }
          f === d && (f = null), (d.sibling.return = d.return), (d = d.sibling);
        }
      }
      break;
    case 19:
      Ze(t, e), st(e), r & 4 && Eu(e);
      break;
    case 21:
      break;
    default:
      Ze(t, e), st(e);
  }
}
function st(e) {
  var t = e.flags;
  if (t & 2) {
    try {
      e: {
        for (var n = e.return; n !== null; ) {
          if (ld(n)) {
            var r = n;
            break e;
          }
          n = n.return;
        }
        throw Error(P(160));
      }
      switch (r.tag) {
        case 5:
          var o = r.stateNode;
          r.flags & 32 && (wr(o, ""), (r.flags &= -33));
          var i = Cu(e);
          bl(e, i, o);
          break;
        case 3:
        case 4:
          var l = r.stateNode.containerInfo,
            s = Cu(e);
          Hl(e, s, l);
          break;
        default:
          throw Error(P(161));
      }
    } catch (a) {
      q(e, e.return, a);
    }
    e.flags &= -3;
  }
  t & 4096 && (e.flags &= -4097);
}
function Nh(e, t, n) {
  (R = e), ud(e);
}
function ud(e, t, n) {
  for (var r = (e.mode & 1) !== 0; R !== null; ) {
    var o = R,
      i = o.child;
    if (o.tag === 22 && r) {
      var l = o.memoizedState !== null || lo;
      if (!l) {
        var s = o.alternate,
          a = (s !== null && s.memoizedState !== null) || we;
        s = lo;
        var u = we;
        if (((lo = l), (we = a) && !u))
          for (R = o; R !== null; )
            (l = R),
              (a = l.child),
              l.tag === 22 && l.memoizedState !== null
                ? Nu(o)
                : a !== null
                ? ((a.return = l), (R = a))
                : Nu(o);
        for (; i !== null; ) (R = i), ud(i), (i = i.sibling);
        (R = o), (lo = s), (we = u);
      }
      _u(e);
    } else
      o.subtreeFlags & 8772 && i !== null ? ((i.return = o), (R = i)) : _u(e);
  }
}
function _u(e) {
  for (; R !== null; ) {
    var t = R;
    if (t.flags & 8772) {
      var n = t.alternate;
      try {
        if (t.flags & 8772)
          switch (t.tag) {
            case 0:
            case 11:
            case 15:
              we || li(5, t);
              break;
            case 1:
              var r = t.stateNode;
              if (t.flags & 4 && !we)
                if (n === null) r.componentDidMount();
                else {
                  var o =
                    t.elementType === t.type
                      ? n.memoizedProps
                      : Je(t.type, n.memoizedProps);
                  r.componentDidUpdate(
                    o,
                    n.memoizedState,
                    r.__reactInternalSnapshotBeforeUpdate
                  );
                }
              var i = t.updateQueue;
              i !== null && uu(t, i, r);
              break;
            case 3:
              var l = t.updateQueue;
              if (l !== null) {
                if (((n = null), t.child !== null))
                  switch (t.child.tag) {
                    case 5:
                      n = t.child.stateNode;
                      break;
                    case 1:
                      n = t.child.stateNode;
                  }
                uu(t, l, n);
              }
              break;
            case 5:
              var s = t.stateNode;
              if (n === null && t.flags & 4) {
                n = s;
                var a = t.memoizedProps;
                switch (t.type) {
                  case "button":
                  case "input":
                  case "select":
                  case "textarea":
                    a.autoFocus && n.focus();
                    break;
                  case "img":
                    a.src && (n.src = a.src);
                }
              }
              break;
            case 6:
              break;
            case 4:
              break;
            case 12:
              break;
            case 13:
              if (t.memoizedState === null) {
                var u = t.alternate;
                if (u !== null) {
                  var f = u.memoizedState;
                  if (f !== null) {
                    var d = f.dehydrated;
                    d !== null && Cr(d);
                  }
                }
              }
              break;
            case 19:
            case 17:
            case 21:
            case 22:
            case 23:
            case 25:
              break;
            default:
              throw Error(P(163));
          }
        we || (t.flags & 512 && Ul(t));
      } catch (h) {
        q(t, t.return, h);
      }
    }
    if (t === e) {
      R = null;
      break;
    }
    if (((n = t.sibling), n !== null)) {
      (n.return = t.return), (R = n);
      break;
    }
    R = t.return;
  }
}
function $u(e) {
  for (; R !== null; ) {
    var t = R;
    if (t === e) {
      R = null;
      break;
    }
    var n = t.sibling;
    if (n !== null) {
      (n.return = t.return), (R = n);
      break;
    }
    R = t.return;
  }
}
function Nu(e) {
  for (; R !== null; ) {
    var t = R;
    try {
      switch (t.tag) {
        case 0:
        case 11:
        case 15:
          var n = t.return;
          try {
            li(4, t);
          } catch (a) {
            q(t, n, a);
          }
          break;
        case 1:
          var r = t.stateNode;
          if (typeof r.componentDidMount == "function") {
            var o = t.return;
            try {
              r.componentDidMount();
            } catch (a) {
              q(t, o, a);
            }
          }
          var i = t.return;
          try {
            Ul(t);
          } catch (a) {
            q(t, i, a);
          }
          break;
        case 5:
          var l = t.return;
          try {
            Ul(t);
          } catch (a) {
            q(t, l, a);
          }
      }
    } catch (a) {
      q(t, t.return, a);
    }
    if (t === e) {
      R = null;
      break;
    }
    var s = t.sibling;
    if (s !== null) {
      (s.return = t.return), (R = s);
      break;
    }
    R = t.return;
  }
}
var Ph = Math.ceil,
  Qo = xt.ReactCurrentDispatcher,
  bs = xt.ReactCurrentOwner,
  be = xt.ReactCurrentBatchConfig,
  D = 0,
  ae = null,
  te = null,
  me = 0,
  Fe = 0,
  _n = bt(0),
  oe = 0,
  Ir = null,
  rn = 0,
  si = 0,
  Qs = 0,
  yr = null,
  Te = null,
  Gs = 0,
  An = 1 / 0,
  pt = null,
  Go = !1,
  Ql = null,
  Dt = null,
  so = !1,
  zt = null,
  Yo = 0,
  vr = 0,
  Gl = null,
  Eo = -1,
  _o = 0;
function $e() {
  return D & 6 ? ee() : Eo !== -1 ? Eo : (Eo = ee());
}
function Vt(e) {
  return e.mode & 1
    ? D & 2 && me !== 0
      ? me & -me
      : fh.transition !== null
      ? (_o === 0 && (_o = Qc()), _o)
      : ((e = A),
        e !== 0 || ((e = window.event), (e = e === void 0 ? 16 : qc(e.type))),
        e)
    : 1;
}
function ot(e, t, n, r) {
  if (50 < vr) throw ((vr = 0), (Gl = null), Error(P(185)));
  Vr(e, n, r),
    (!(D & 2) || e !== ae) &&
      (e === ae && (!(D & 2) && (si |= n), oe === 4 && Tt(e, me)),
      Ie(e, r),
      n === 1 && D === 0 && !(t.mode & 1) && ((An = ee() + 500), ri && Qt()));
}
function Ie(e, t) {
  var n = e.callbackNode;
  fm(e, t);
  var r = Ro(e, e === ae ? me : 0);
  if (r === 0)
    n !== null && Fa(n), (e.callbackNode = null), (e.callbackPriority = 0);
  else if (((t = r & -r), e.callbackPriority !== t)) {
    if ((n != null && Fa(n), t === 1))
      e.tag === 0 ? ch(Pu.bind(null, e)) : wf(Pu.bind(null, e)),
        lh(function () {
          !(D & 6) && Qt();
        }),
        (n = null);
    else {
      switch (Gc(r)) {
        case 1:
          n = ws;
          break;
        case 4:
          n = Hc;
          break;
        case 16:
          n = To;
          break;
        case 536870912:
          n = bc;
          break;
        default:
          n = To;
      }
      n = vd(n, cd.bind(null, e));
    }
    (e.callbackPriority = t), (e.callbackNode = n);
  }
}
function cd(e, t) {
  if (((Eo = -1), (_o = 0), D & 6)) throw Error(P(327));
  var n = e.callbackNode;
  if (zn() && e.callbackNode !== n) return null;
  var r = Ro(e, e === ae ? me : 0);
  if (r === 0) return null;
  if (r & 30 || r & e.expiredLanes || t) t = Ko(e, r);
  else {
    t = r;
    var o = D;
    D |= 2;
    var i = dd();
    (ae !== e || me !== t) && ((pt = null), (An = ee() + 500), Jt(e, t));
    do
      try {
        Rh();
        break;
      } catch (s) {
        fd(e, s);
      }
    while (!0);
    zs(),
      (Qo.current = i),
      (D = o),
      te !== null ? (t = 0) : ((ae = null), (me = 0), (t = oe));
  }
  if (t !== 0) {
    if (
      (t === 2 && ((o = Sl(e)), o !== 0 && ((r = o), (t = Yl(e, o)))), t === 1)
    )
      throw ((n = Ir), Jt(e, 0), Tt(e, r), Ie(e, ee()), n);
    if (t === 6) Tt(e, r);
    else {
      if (
        ((o = e.current.alternate),
        !(r & 30) &&
          !jh(o) &&
          ((t = Ko(e, r)),
          t === 2 && ((i = Sl(e)), i !== 0 && ((r = i), (t = Yl(e, i)))),
          t === 1))
      )
        throw ((n = Ir), Jt(e, 0), Tt(e, r), Ie(e, ee()), n);
      switch (((e.finishedWork = o), (e.finishedLanes = r), t)) {
        case 0:
        case 1:
          throw Error(P(345));
        case 2:
          Yt(e, Te, pt);
          break;
        case 3:
          if (
            (Tt(e, r), (r & 130023424) === r && ((t = Gs + 500 - ee()), 10 < t))
          ) {
            if (Ro(e, 0) !== 0) break;
            if (((o = e.suspendedLanes), (o & r) !== r)) {
              $e(), (e.pingedLanes |= e.suspendedLanes & o);
              break;
            }
            e.timeoutHandle = Pl(Yt.bind(null, e, Te, pt), t);
            break;
          }
          Yt(e, Te, pt);
          break;
        case 4:
          if ((Tt(e, r), (r & 4194240) === r)) break;
          for (t = e.eventTimes, o = -1; 0 < r; ) {
            var l = 31 - rt(r);
            (i = 1 << l), (l = t[l]), l > o && (o = l), (r &= ~i);
          }
          if (
            ((r = o),
            (r = ee() - r),
            (r =
              (120 > r
                ? 120
                : 480 > r
                ? 480
                : 1080 > r
                ? 1080
                : 1920 > r
                ? 1920
                : 3e3 > r
                ? 3e3
                : 4320 > r
                ? 4320
                : 1960 * Ph(r / 1960)) - r),
            10 < r)
          ) {
            e.timeoutHandle = Pl(Yt.bind(null, e, Te, pt), r);
            break;
          }
          Yt(e, Te, pt);
          break;
        case 5:
          Yt(e, Te, pt);
          break;
        default:
          throw Error(P(329));
      }
    }
  }
  return Ie(e, ee()), e.callbackNode === n ? cd.bind(null, e) : null;
}
function Yl(e, t) {
  var n = yr;
  return (
    e.current.memoizedState.isDehydrated && (Jt(e, t).flags |= 256),
    (e = Ko(e, t)),
    e !== 2 && ((t = Te), (Te = n), t !== null && Kl(t)),
    e
  );
}
function Kl(e) {
  Te === null ? (Te = e) : Te.push.apply(Te, e);
}
function jh(e) {
  for (var t = e; ; ) {
    if (t.flags & 16384) {
      var n = t.updateQueue;
      if (n !== null && ((n = n.stores), n !== null))
        for (var r = 0; r < n.length; r++) {
          var o = n[r],
            i = o.getSnapshot;
          o = o.value;
          try {
            if (!lt(i(), o)) return !1;
          } catch {
            return !1;
          }
        }
    }
    if (((n = t.child), t.subtreeFlags & 16384 && n !== null))
      (n.return = t), (t = n);
    else {
      if (t === e) break;
      for (; t.sibling === null; ) {
        if (t.return === null || t.return === e) return !0;
        t = t.return;
      }
      (t.sibling.return = t.return), (t = t.sibling);
    }
  }
  return !0;
}
function Tt(e, t) {
  for (
    t &= ~Qs,
      t &= ~si,
      e.suspendedLanes |= t,
      e.pingedLanes &= ~t,
      e = e.expirationTimes;
    0 < t;

  ) {
    var n = 31 - rt(t),
      r = 1 << n;
    (e[n] = -1), (t &= ~r);
  }
}
function Pu(e) {
  if (D & 6) throw Error(P(327));
  zn();
  var t = Ro(e, 0);
  if (!(t & 1)) return Ie(e, ee()), null;
  var n = Ko(e, t);
  if (e.tag !== 0 && n === 2) {
    var r = Sl(e);
    r !== 0 && ((t = r), (n = Yl(e, r)));
  }
  if (n === 1) throw ((n = Ir), Jt(e, 0), Tt(e, t), Ie(e, ee()), n);
  if (n === 6) throw Error(P(345));
  return (
    (e.finishedWork = e.current.alternate),
    (e.finishedLanes = t),
    Yt(e, Te, pt),
    Ie(e, ee()),
    null
  );
}
function Ys(e, t) {
  var n = D;
  D |= 1;
  try {
    return e(t);
  } finally {
    (D = n), D === 0 && ((An = ee() + 500), ri && Qt());
  }
}
function on(e) {
  zt !== null && zt.tag === 0 && !(D & 6) && zn();
  var t = D;
  D |= 1;
  var n = be.transition,
    r = A;
  try {
    if (((be.transition = null), (A = 1), e)) return e();
  } finally {
    (A = r), (be.transition = n), (D = t), !(D & 6) && Qt();
  }
}
function Ks() {
  (Fe = _n.current), G(_n);
}
function Jt(e, t) {
  (e.finishedWork = null), (e.finishedLanes = 0);
  var n = e.timeoutHandle;
  if ((n !== -1 && ((e.timeoutHandle = -1), ih(n)), te !== null))
    for (n = te.return; n !== null; ) {
      var r = n;
      switch ((js(r), r.tag)) {
        case 1:
          (r = r.type.childContextTypes), r != null && Fo();
          break;
        case 3:
          Dn(), G(ze), G(xe), Ds();
          break;
        case 5:
          Ms(r);
          break;
        case 4:
          Dn();
          break;
        case 13:
          G(K);
          break;
        case 19:
          G(K);
          break;
        case 10:
          Ls(r.type._context);
          break;
        case 22:
        case 23:
          Ks();
      }
      n = n.return;
    }
  if (
    ((ae = e),
    (te = e = At(e.current, null)),
    (me = Fe = t),
    (oe = 0),
    (Ir = null),
    (Qs = si = rn = 0),
    (Te = yr = null),
    Xt !== null)
  ) {
    for (t = 0; t < Xt.length; t++)
      if (((n = Xt[t]), (r = n.interleaved), r !== null)) {
        n.interleaved = null;
        var o = r.next,
          i = n.pending;
        if (i !== null) {
          var l = i.next;
          (i.next = o), (r.next = l);
        }
        n.pending = r;
      }
    Xt = null;
  }
  return e;
}
function fd(e, t) {
  do {
    var n = te;
    try {
      if ((zs(), (ko.current = bo), Ho)) {
        for (var r = X.memoizedState; r !== null; ) {
          var o = r.queue;
          o !== null && (o.pending = null), (r = r.next);
        }
        Ho = !1;
      }
      if (
        ((nn = 0),
        (se = re = X = null),
        (mr = !1),
        (Rr = 0),
        (bs.current = null),
        n === null || n.return === null)
      ) {
        (oe = 1), (Ir = t), (te = null);
        break;
      }
      e: {
        var i = e,
          l = n.return,
          s = n,
          a = t;
        if (
          ((t = me),
          (s.flags |= 32768),
          a !== null && typeof a == "object" && typeof a.then == "function")
        ) {
          var u = a,
            f = s,
            d = f.tag;
          if (!(f.mode & 1) && (d === 0 || d === 11 || d === 15)) {
            var h = f.alternate;
            h
              ? ((f.updateQueue = h.updateQueue),
                (f.memoizedState = h.memoizedState),
                (f.lanes = h.lanes))
              : ((f.updateQueue = null), (f.memoizedState = null));
          }
          var g = hu(l);
          if (g !== null) {
            (g.flags &= -257),
              yu(g, l, s, i, t),
              g.mode & 1 && mu(i, u, t),
              (t = g),
              (a = u);
            var y = t.updateQueue;
            if (y === null) {
              var v = new Set();
              v.add(a), (t.updateQueue = v);
            } else y.add(a);
            break e;
          } else {
            if (!(t & 1)) {
              mu(i, u, t), Xs();
              break e;
            }
            a = Error(P(426));
          }
        } else if (Y && s.mode & 1) {
          var C = hu(l);
          if (C !== null) {
            !(C.flags & 65536) && (C.flags |= 256),
              yu(C, l, s, i, t),
              Ts(Vn(a, s));
            break e;
          }
        }
        (i = a = Vn(a, s)),
          oe !== 4 && (oe = 2),
          yr === null ? (yr = [i]) : yr.push(i),
          (i = l);
        do {
          switch (i.tag) {
            case 3:
              (i.flags |= 65536), (t &= -t), (i.lanes |= t);
              var m = Yf(i, a, t);
              au(i, m);
              break e;
            case 1:
              s = a;
              var c = i.type,
                p = i.stateNode;
              if (
                !(i.flags & 128) &&
                (typeof c.getDerivedStateFromError == "function" ||
                  (p !== null &&
                    typeof p.componentDidCatch == "function" &&
                    (Dt === null || !Dt.has(p))))
              ) {
                (i.flags |= 65536), (t &= -t), (i.lanes |= t);
                var S = Kf(i, s, t);
                au(i, S);
                break e;
              }
          }
          i = i.return;
        } while (i !== null);
      }
      md(n);
    } catch (_) {
      (t = _), te === n && n !== null && (te = n = n.return);
      continue;
    }
    break;
  } while (!0);
}
function dd() {
  var e = Qo.current;
  return (Qo.current = bo), e === null ? bo : e;
}
function Xs() {
  (oe === 0 || oe === 3 || oe === 2) && (oe = 4),
    ae === null || (!(rn & 268435455) && !(si & 268435455)) || Tt(ae, me);
}
function Ko(e, t) {
  var n = D;
  D |= 2;
  var r = dd();
  (ae !== e || me !== t) && ((pt = null), Jt(e, t));
  do
    try {
      Th();
      break;
    } catch (o) {
      fd(e, o);
    }
  while (!0);
  if ((zs(), (D = n), (Qo.current = r), te !== null)) throw Error(P(261));
  return (ae = null), (me = 0), oe;
}
function Th() {
  for (; te !== null; ) pd(te);
}
function Rh() {
  for (; te !== null && !nm(); ) pd(te);
}
function pd(e) {
  var t = yd(e.alternate, e, Fe);
  (e.memoizedProps = e.pendingProps),
    t === null ? md(e) : (te = t),
    (bs.current = null);
}
function md(e) {
  var t = e;
  do {
    var n = t.alternate;
    if (((e = t.return), t.flags & 32768)) {
      if (((n = Eh(n, t)), n !== null)) {
        (n.flags &= 32767), (te = n);
        return;
      }
      if (e !== null)
        (e.flags |= 32768), (e.subtreeFlags = 0), (e.deletions = null);
      else {
        (oe = 6), (te = null);
        return;
      }
    } else if (((n = Ch(n, t, Fe)), n !== null)) {
      te = n;
      return;
    }
    if (((t = t.sibling), t !== null)) {
      te = t;
      return;
    }
    te = t = e;
  } while (t !== null);
  oe === 0 && (oe = 5);
}
function Yt(e, t, n) {
  var r = A,
    o = be.transition;
  try {
    (be.transition = null), (A = 1), zh(e, t, n, r);
  } finally {
    (be.transition = o), (A = r);
  }
  return null;
}
function zh(e, t, n, r) {
  do zn();
  while (zt !== null);
  if (D & 6) throw Error(P(327));
  n = e.finishedWork;
  var o = e.finishedLanes;
  if (n === null) return null;
  if (((e.finishedWork = null), (e.finishedLanes = 0), n === e.current))
    throw Error(P(177));
  (e.callbackNode = null), (e.callbackPriority = 0);
  var i = n.lanes | n.childLanes;
  if (
    (dm(e, i),
    e === ae && ((te = ae = null), (me = 0)),
    (!(n.subtreeFlags & 2064) && !(n.flags & 2064)) ||
      so ||
      ((so = !0),
      vd(To, function () {
        return zn(), null;
      })),
    (i = (n.flags & 15990) !== 0),
    n.subtreeFlags & 15990 || i)
  ) {
    (i = be.transition), (be.transition = null);
    var l = A;
    A = 1;
    var s = D;
    (D |= 4),
      (bs.current = null),
      $h(e, n),
      ad(n, e),
      Jm($l),
      (zo = !!_l),
      ($l = _l = null),
      (e.current = n),
      Nh(n),
      rm(),
      (D = s),
      (A = l),
      (be.transition = i);
  } else e.current = n;
  if (
    (so && ((so = !1), (zt = e), (Yo = o)),
    (i = e.pendingLanes),
    i === 0 && (Dt = null),
    lm(n.stateNode),
    Ie(e, ee()),
    t !== null)
  )
    for (r = e.onRecoverableError, n = 0; n < t.length; n++)
      (o = t[n]), r(o.value, { componentStack: o.stack, digest: o.digest });
  if (Go) throw ((Go = !1), (e = Ql), (Ql = null), e);
  return (
    Yo & 1 && e.tag !== 0 && zn(),
    (i = e.pendingLanes),
    i & 1 ? (e === Gl ? vr++ : ((vr = 0), (Gl = e))) : (vr = 0),
    Qt(),
    null
  );
}
function zn() {
  if (zt !== null) {
    var e = Gc(Yo),
      t = be.transition,
      n = A;
    try {
      if (((be.transition = null), (A = 16 > e ? 16 : e), zt === null))
        var r = !1;
      else {
        if (((e = zt), (zt = null), (Yo = 0), D & 6)) throw Error(P(331));
        var o = D;
        for (D |= 4, R = e.current; R !== null; ) {
          var i = R,
            l = i.child;
          if (R.flags & 16) {
            var s = i.deletions;
            if (s !== null) {
              for (var a = 0; a < s.length; a++) {
                var u = s[a];
                for (R = u; R !== null; ) {
                  var f = R;
                  switch (f.tag) {
                    case 0:
                    case 11:
                    case 15:
                      hr(8, f, i);
                  }
                  var d = f.child;
                  if (d !== null) (d.return = f), (R = d);
                  else
                    for (; R !== null; ) {
                      f = R;
                      var h = f.sibling,
                        g = f.return;
                      if ((id(f), f === u)) {
                        R = null;
                        break;
                      }
                      if (h !== null) {
                        (h.return = g), (R = h);
                        break;
                      }
                      R = g;
                    }
                }
              }
              var y = i.alternate;
              if (y !== null) {
                var v = y.child;
                if (v !== null) {
                  y.child = null;
                  do {
                    var C = v.sibling;
                    (v.sibling = null), (v = C);
                  } while (v !== null);
                }
              }
              R = i;
            }
          }
          if (i.subtreeFlags & 2064 && l !== null) (l.return = i), (R = l);
          else
            e: for (; R !== null; ) {
              if (((i = R), i.flags & 2048))
                switch (i.tag) {
                  case 0:
                  case 11:
                  case 15:
                    hr(9, i, i.return);
                }
              var m = i.sibling;
              if (m !== null) {
                (m.return = i.return), (R = m);
                break e;
              }
              R = i.return;
            }
        }
        var c = e.current;
        for (R = c; R !== null; ) {
          l = R;
          var p = l.child;
          if (l.subtreeFlags & 2064 && p !== null) (p.return = l), (R = p);
          else
            e: for (l = c; R !== null; ) {
              if (((s = R), s.flags & 2048))
                try {
                  switch (s.tag) {
                    case 0:
                    case 11:
                    case 15:
                      li(9, s);
                  }
                } catch (_) {
                  q(s, s.return, _);
                }
              if (s === l) {
                R = null;
                break e;
              }
              var S = s.sibling;
              if (S !== null) {
                (S.return = s.return), (R = S);
                break e;
              }
              R = s.return;
            }
        }
        if (
          ((D = o), Qt(), ct && typeof ct.onPostCommitFiberRoot == "function")
        )
          try {
            ct.onPostCommitFiberRoot(Jo, e);
          } catch {}
        r = !0;
      }
      return r;
    } finally {
      (A = n), (be.transition = t);
    }
  }
  return !1;
}
function ju(e, t, n) {
  (t = Vn(n, t)),
    (t = Yf(e, t, 1)),
    (e = Mt(e, t, 1)),
    (t = $e()),
    e !== null && (Vr(e, 1, t), Ie(e, t));
}
function q(e, t, n) {
  if (e.tag === 3) ju(e, e, n);
  else
    for (; t !== null; ) {
      if (t.tag === 3) {
        ju(t, e, n);
        break;
      } else if (t.tag === 1) {
        var r = t.stateNode;
        if (
          typeof t.type.getDerivedStateFromError == "function" ||
          (typeof r.componentDidCatch == "function" &&
            (Dt === null || !Dt.has(r)))
        ) {
          (e = Vn(n, e)),
            (e = Kf(t, e, 1)),
            (t = Mt(t, e, 1)),
            (e = $e()),
            t !== null && (Vr(t, 1, e), Ie(t, e));
          break;
        }
      }
      t = t.return;
    }
}
function Lh(e, t, n) {
  var r = e.pingCache;
  r !== null && r.delete(t),
    (t = $e()),
    (e.pingedLanes |= e.suspendedLanes & n),
    ae === e &&
      (me & n) === n &&
      (oe === 4 || (oe === 3 && (me & 130023424) === me && 500 > ee() - Gs)
        ? Jt(e, 0)
        : (Qs |= n)),
    Ie(e, t);
}
function hd(e, t) {
  t === 0 &&
    (e.mode & 1
      ? ((t = Zr), (Zr <<= 1), !(Zr & 130023424) && (Zr = 4194304))
      : (t = 1));
  var n = $e();
  (e = St(e, t)), e !== null && (Vr(e, t, n), Ie(e, n));
}
function Ih(e) {
  var t = e.memoizedState,
    n = 0;
  t !== null && (n = t.retryLane), hd(e, n);
}
function Oh(e, t) {
  var n = 0;
  switch (e.tag) {
    case 13:
      var r = e.stateNode,
        o = e.memoizedState;
      o !== null && (n = o.retryLane);
      break;
    case 19:
      r = e.stateNode;
      break;
    default:
      throw Error(P(314));
  }
  r !== null && r.delete(t), hd(e, n);
}
var yd;
yd = function (e, t, n) {
  if (e !== null)
    if (e.memoizedProps !== t.pendingProps || ze.current) Re = !0;
    else {
      if (!(e.lanes & n) && !(t.flags & 128)) return (Re = !1), xh(e, t, n);
      Re = !!(e.flags & 131072);
    }
  else (Re = !1), Y && t.flags & 1048576 && Sf(t, Vo, t.index);
  switch (((t.lanes = 0), t.tag)) {
    case 2:
      var r = t.type;
      Co(e, t), (e = t.pendingProps);
      var o = On(t, xe.current);
      Rn(t, n), (o = As(null, t, r, e, o, n));
      var i = Bs();
      return (
        (t.flags |= 1),
        typeof o == "object" &&
        o !== null &&
        typeof o.render == "function" &&
        o.$$typeof === void 0
          ? ((t.tag = 1),
            (t.memoizedState = null),
            (t.updateQueue = null),
            Le(r) ? ((i = !0), Mo(t)) : (i = !1),
            (t.memoizedState =
              o.state !== null && o.state !== void 0 ? o.state : null),
            Os(t),
            (o.updater = ii),
            (t.stateNode = o),
            (o._reactInternals = t),
            Ol(t, r, e, n),
            (t = Dl(null, t, r, !0, i, n)))
          : ((t.tag = 0), Y && i && Ps(t), _e(null, t, o, n), (t = t.child)),
        t
      );
    case 16:
      r = t.elementType;
      e: {
        switch (
          (Co(e, t),
          (e = t.pendingProps),
          (o = r._init),
          (r = o(r._payload)),
          (t.type = r),
          (o = t.tag = Mh(r)),
          (e = Je(r, e)),
          o)
        ) {
          case 0:
            t = Ml(null, t, r, e, n);
            break e;
          case 1:
            t = wu(null, t, r, e, n);
            break e;
          case 11:
            t = vu(null, t, r, e, n);
            break e;
          case 14:
            t = gu(null, t, r, Je(r.type, e), n);
            break e;
        }
        throw Error(P(306, r, ""));
      }
      return t;
    case 0:
      return (
        (r = t.type),
        (o = t.pendingProps),
        (o = t.elementType === r ? o : Je(r, o)),
        Ml(e, t, r, o, n)
      );
    case 1:
      return (
        (r = t.type),
        (o = t.pendingProps),
        (o = t.elementType === r ? o : Je(r, o)),
        wu(e, t, r, o, n)
      );
    case 3:
      e: {
        if ((qf(t), e === null)) throw Error(P(387));
        (r = t.pendingProps),
          (i = t.memoizedState),
          (o = i.element),
          $f(e, t),
          Wo(t, r, null, n);
        var l = t.memoizedState;
        if (((r = l.element), i.isDehydrated))
          if (
            ((i = {
              element: r,
              isDehydrated: !1,
              cache: l.cache,
              pendingSuspenseBoundaries: l.pendingSuspenseBoundaries,
              transitions: l.transitions,
            }),
            (t.updateQueue.baseState = i),
            (t.memoizedState = i),
            t.flags & 256)
          ) {
            (o = Vn(Error(P(423)), t)), (t = Su(e, t, r, n, o));
            break e;
          } else if (r !== o) {
            (o = Vn(Error(P(424)), t)), (t = Su(e, t, r, n, o));
            break e;
          } else
            for (
              Me = Ft(t.stateNode.containerInfo.firstChild),
                De = t,
                Y = !0,
                et = null,
                n = Ef(t, null, r, n),
                t.child = n;
              n;

            )
              (n.flags = (n.flags & -3) | 4096), (n = n.sibling);
        else {
          if ((Fn(), r === o)) {
            t = kt(e, t, n);
            break e;
          }
          _e(e, t, r, n);
        }
        t = t.child;
      }
      return t;
    case 5:
      return (
        Nf(t),
        e === null && zl(t),
        (r = t.type),
        (o = t.pendingProps),
        (i = e !== null ? e.memoizedProps : null),
        (l = o.children),
        Nl(r, o) ? (l = null) : i !== null && Nl(r, i) && (t.flags |= 32),
        Jf(e, t),
        _e(e, t, l, n),
        t.child
      );
    case 6:
      return e === null && zl(t), null;
    case 13:
      return ed(e, t, n);
    case 4:
      return (
        Fs(t, t.stateNode.containerInfo),
        (r = t.pendingProps),
        e === null ? (t.child = Mn(t, null, r, n)) : _e(e, t, r, n),
        t.child
      );
    case 11:
      return (
        (r = t.type),
        (o = t.pendingProps),
        (o = t.elementType === r ? o : Je(r, o)),
        vu(e, t, r, o, n)
      );
    case 7:
      return _e(e, t, t.pendingProps, n), t.child;
    case 8:
      return _e(e, t, t.pendingProps.children, n), t.child;
    case 12:
      return _e(e, t, t.pendingProps.children, n), t.child;
    case 10:
      e: {
        if (
          ((r = t.type._context),
          (o = t.pendingProps),
          (i = t.memoizedProps),
          (l = o.value),
          U(Ao, r._currentValue),
          (r._currentValue = l),
          i !== null)
        )
          if (lt(i.value, l)) {
            if (i.children === o.children && !ze.current) {
              t = kt(e, t, n);
              break e;
            }
          } else
            for (i = t.child, i !== null && (i.return = t); i !== null; ) {
              var s = i.dependencies;
              if (s !== null) {
                l = i.child;
                for (var a = s.firstContext; a !== null; ) {
                  if (a.context === r) {
                    if (i.tag === 1) {
                      (a = vt(-1, n & -n)), (a.tag = 2);
                      var u = i.updateQueue;
                      if (u !== null) {
                        u = u.shared;
                        var f = u.pending;
                        f === null
                          ? (a.next = a)
                          : ((a.next = f.next), (f.next = a)),
                          (u.pending = a);
                      }
                    }
                    (i.lanes |= n),
                      (a = i.alternate),
                      a !== null && (a.lanes |= n),
                      Ll(i.return, n, t),
                      (s.lanes |= n);
                    break;
                  }
                  a = a.next;
                }
              } else if (i.tag === 10) l = i.type === t.type ? null : i.child;
              else if (i.tag === 18) {
                if (((l = i.return), l === null)) throw Error(P(341));
                (l.lanes |= n),
                  (s = l.alternate),
                  s !== null && (s.lanes |= n),
                  Ll(l, n, t),
                  (l = i.sibling);
              } else l = i.child;
              if (l !== null) l.return = i;
              else
                for (l = i; l !== null; ) {
                  if (l === t) {
                    l = null;
                    break;
                  }
                  if (((i = l.sibling), i !== null)) {
                    (i.return = l.return), (l = i);
                    break;
                  }
                  l = l.return;
                }
              i = l;
            }
        _e(e, t, o.children, n), (t = t.child);
      }
      return t;
    case 9:
      return (
        (o = t.type),
        (r = t.pendingProps.children),
        Rn(t, n),
        (o = Qe(o)),
        (r = r(o)),
        (t.flags |= 1),
        _e(e, t, r, n),
        t.child
      );
    case 14:
      return (
        (r = t.type),
        (o = Je(r, t.pendingProps)),
        (o = Je(r.type, o)),
        gu(e, t, r, o, n)
      );
    case 15:
      return Xf(e, t, t.type, t.pendingProps, n);
    case 17:
      return (
        (r = t.type),
        (o = t.pendingProps),
        (o = t.elementType === r ? o : Je(r, o)),
        Co(e, t),
        (t.tag = 1),
        Le(r) ? ((e = !0), Mo(t)) : (e = !1),
        Rn(t, n),
        Gf(t, r, o),
        Ol(t, r, o, n),
        Dl(null, t, r, !0, e, n)
      );
    case 19:
      return td(e, t, n);
    case 22:
      return Zf(e, t, n);
  }
  throw Error(P(156, t.tag));
};
function vd(e, t) {
  return Uc(e, t);
}
function Fh(e, t, n, r) {
  (this.tag = e),
    (this.key = n),
    (this.sibling =
      this.child =
      this.return =
      this.stateNode =
      this.type =
      this.elementType =
        null),
    (this.index = 0),
    (this.ref = null),
    (this.pendingProps = t),
    (this.dependencies =
      this.memoizedState =
      this.updateQueue =
      this.memoizedProps =
        null),
    (this.mode = r),
    (this.subtreeFlags = this.flags = 0),
    (this.deletions = null),
    (this.childLanes = this.lanes = 0),
    (this.alternate = null);
}
function He(e, t, n, r) {
  return new Fh(e, t, n, r);
}
function Zs(e) {
  return (e = e.prototype), !(!e || !e.isReactComponent);
}
function Mh(e) {
  if (typeof e == "function") return Zs(e) ? 1 : 0;
  if (e != null) {
    if (((e = e.$$typeof), e === ys)) return 11;
    if (e === vs) return 14;
  }
  return 2;
}
function At(e, t) {
  var n = e.alternate;
  return (
    n === null
      ? ((n = He(e.tag, t, e.key, e.mode)),
        (n.elementType = e.elementType),
        (n.type = e.type),
        (n.stateNode = e.stateNode),
        (n.alternate = e),
        (e.alternate = n))
      : ((n.pendingProps = t),
        (n.type = e.type),
        (n.flags = 0),
        (n.subtreeFlags = 0),
        (n.deletions = null)),
    (n.flags = e.flags & 14680064),
    (n.childLanes = e.childLanes),
    (n.lanes = e.lanes),
    (n.child = e.child),
    (n.memoizedProps = e.memoizedProps),
    (n.memoizedState = e.memoizedState),
    (n.updateQueue = e.updateQueue),
    (t = e.dependencies),
    (n.dependencies =
      t === null ? null : { lanes: t.lanes, firstContext: t.firstContext }),
    (n.sibling = e.sibling),
    (n.index = e.index),
    (n.ref = e.ref),
    n
  );
}
function $o(e, t, n, r, o, i) {
  var l = 2;
  if (((r = e), typeof e == "function")) Zs(e) && (l = 1);
  else if (typeof e == "string") l = 5;
  else
    e: switch (e) {
      case hn:
        return qt(n.children, o, i, t);
      case hs:
        (l = 8), (o |= 8);
        break;
      case il:
        return (
          (e = He(12, n, t, o | 2)), (e.elementType = il), (e.lanes = i), e
        );
      case ll:
        return (e = He(13, n, t, o)), (e.elementType = ll), (e.lanes = i), e;
      case sl:
        return (e = He(19, n, t, o)), (e.elementType = sl), (e.lanes = i), e;
      case $c:
        return ai(n, o, i, t);
      default:
        if (typeof e == "object" && e !== null)
          switch (e.$$typeof) {
            case Ec:
              l = 10;
              break e;
            case _c:
              l = 9;
              break e;
            case ys:
              l = 11;
              break e;
            case vs:
              l = 14;
              break e;
            case Nt:
              (l = 16), (r = null);
              break e;
          }
        throw Error(P(130, e == null ? e : typeof e, ""));
    }
  return (
    (t = He(l, n, t, o)), (t.elementType = e), (t.type = r), (t.lanes = i), t
  );
}
function qt(e, t, n, r) {
  return (e = He(7, e, r, t)), (e.lanes = n), e;
}
function ai(e, t, n, r) {
  return (
    (e = He(22, e, r, t)),
    (e.elementType = $c),
    (e.lanes = n),
    (e.stateNode = { isHidden: !1 }),
    e
  );
}
function Yi(e, t, n) {
  return (e = He(6, e, null, t)), (e.lanes = n), e;
}
function Ki(e, t, n) {
  return (
    (t = He(4, e.children !== null ? e.children : [], e.key, t)),
    (t.lanes = n),
    (t.stateNode = {
      containerInfo: e.containerInfo,
      pendingChildren: null,
      implementation: e.implementation,
    }),
    t
  );
}
function Dh(e, t, n, r, o) {
  (this.tag = t),
    (this.containerInfo = e),
    (this.finishedWork =
      this.pingCache =
      this.current =
      this.pendingChildren =
        null),
    (this.timeoutHandle = -1),
    (this.callbackNode = this.pendingContext = this.context = null),
    (this.callbackPriority = 0),
    (this.eventTimes = ji(0)),
    (this.expirationTimes = ji(-1)),
    (this.entangledLanes =
      this.finishedLanes =
      this.mutableReadLanes =
      this.expiredLanes =
      this.pingedLanes =
      this.suspendedLanes =
      this.pendingLanes =
        0),
    (this.entanglements = ji(0)),
    (this.identifierPrefix = r),
    (this.onRecoverableError = o),
    (this.mutableSourceEagerHydrationData = null);
}
function Js(e, t, n, r, o, i, l, s, a) {
  return (
    (e = new Dh(e, t, n, s, a)),
    t === 1 ? ((t = 1), i === !0 && (t |= 8)) : (t = 0),
    (i = He(3, null, null, t)),
    (e.current = i),
    (i.stateNode = e),
    (i.memoizedState = {
      element: r,
      isDehydrated: n,
      cache: null,
      transitions: null,
      pendingSuspenseBoundaries: null,
    }),
    Os(i),
    e
  );
}
function Vh(e, t, n) {
  var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
  return {
    $$typeof: mn,
    key: r == null ? null : "" + r,
    children: e,
    containerInfo: t,
    implementation: n,
  };
}
function gd(e) {
  if (!e) return Wt;
  e = e._reactInternals;
  e: {
    if (sn(e) !== e || e.tag !== 1) throw Error(P(170));
    var t = e;
    do {
      switch (t.tag) {
        case 3:
          t = t.stateNode.context;
          break e;
        case 1:
          if (Le(t.type)) {
            t = t.stateNode.__reactInternalMemoizedMergedChildContext;
            break e;
          }
      }
      t = t.return;
    } while (t !== null);
    throw Error(P(171));
  }
  if (e.tag === 1) {
    var n = e.type;
    if (Le(n)) return gf(e, n, t);
  }
  return t;
}
function wd(e, t, n, r, o, i, l, s, a) {
  return (
    (e = Js(n, r, !0, e, o, i, l, s, a)),
    (e.context = gd(null)),
    (n = e.current),
    (r = $e()),
    (o = Vt(n)),
    (i = vt(r, o)),
    (i.callback = t ?? null),
    Mt(n, i, o),
    (e.current.lanes = o),
    Vr(e, o, r),
    Ie(e, r),
    e
  );
}
function ui(e, t, n, r) {
  var o = t.current,
    i = $e(),
    l = Vt(o);
  return (
    (n = gd(n)),
    t.context === null ? (t.context = n) : (t.pendingContext = n),
    (t = vt(i, l)),
    (t.payload = { element: e }),
    (r = r === void 0 ? null : r),
    r !== null && (t.callback = r),
    (e = Mt(o, t, l)),
    e !== null && (ot(e, o, l, i), So(e, o, l)),
    l
  );
}
function Xo(e) {
  if (((e = e.current), !e.child)) return null;
  switch (e.child.tag) {
    case 5:
      return e.child.stateNode;
    default:
      return e.child.stateNode;
  }
}
function Tu(e, t) {
  if (((e = e.memoizedState), e !== null && e.dehydrated !== null)) {
    var n = e.retryLane;
    e.retryLane = n !== 0 && n < t ? n : t;
  }
}
function qs(e, t) {
  Tu(e, t), (e = e.alternate) && Tu(e, t);
}
function Ah() {
  return null;
}
var Sd =
  typeof reportError == "function"
    ? reportError
    : function (e) {
        console.error(e);
      };
function ea(e) {
  this._internalRoot = e;
}
ci.prototype.render = ea.prototype.render = function (e) {
  var t = this._internalRoot;
  if (t === null) throw Error(P(409));
  ui(e, t, null, null);
};
ci.prototype.unmount = ea.prototype.unmount = function () {
  var e = this._internalRoot;
  if (e !== null) {
    this._internalRoot = null;
    var t = e.containerInfo;
    on(function () {
      ui(null, e, null, null);
    }),
      (t[wt] = null);
  }
};
function ci(e) {
  this._internalRoot = e;
}
ci.prototype.unstable_scheduleHydration = function (e) {
  if (e) {
    var t = Xc();
    e = { blockedOn: null, target: e, priority: t };
    for (var n = 0; n < jt.length && t !== 0 && t < jt[n].priority; n++);
    jt.splice(n, 0, e), n === 0 && Jc(e);
  }
};
function ta(e) {
  return !(!e || (e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11));
}
function fi(e) {
  return !(
    !e ||
    (e.nodeType !== 1 &&
      e.nodeType !== 9 &&
      e.nodeType !== 11 &&
      (e.nodeType !== 8 || e.nodeValue !== " react-mount-point-unstable "))
  );
}
function Ru() {}
function Bh(e, t, n, r, o) {
  if (o) {
    if (typeof r == "function") {
      var i = r;
      r = function () {
        var u = Xo(l);
        i.call(u);
      };
    }
    var l = wd(t, r, e, 0, null, !1, !1, "", Ru);
    return (
      (e._reactRootContainer = l),
      (e[wt] = l.current),
      $r(e.nodeType === 8 ? e.parentNode : e),
      on(),
      l
    );
  }
  for (; (o = e.lastChild); ) e.removeChild(o);
  if (typeof r == "function") {
    var s = r;
    r = function () {
      var u = Xo(a);
      s.call(u);
    };
  }
  var a = Js(e, 0, !1, null, null, !1, !1, "", Ru);
  return (
    (e._reactRootContainer = a),
    (e[wt] = a.current),
    $r(e.nodeType === 8 ? e.parentNode : e),
    on(function () {
      ui(t, a, n, r);
    }),
    a
  );
}
function di(e, t, n, r, o) {
  var i = n._reactRootContainer;
  if (i) {
    var l = i;
    if (typeof o == "function") {
      var s = o;
      o = function () {
        var a = Xo(l);
        s.call(a);
      };
    }
    ui(t, l, e, o);
  } else l = Bh(n, t, e, o, r);
  return Xo(l);
}
Yc = function (e) {
  switch (e.tag) {
    case 3:
      var t = e.stateNode;
      if (t.current.memoizedState.isDehydrated) {
        var n = lr(t.pendingLanes);
        n !== 0 &&
          (Ss(t, n | 1), Ie(t, ee()), !(D & 6) && ((An = ee() + 500), Qt()));
      }
      break;
    case 13:
      on(function () {
        var r = St(e, 1);
        if (r !== null) {
          var o = $e();
          ot(r, e, 1, o);
        }
      }),
        qs(e, 1);
  }
};
ks = function (e) {
  if (e.tag === 13) {
    var t = St(e, 134217728);
    if (t !== null) {
      var n = $e();
      ot(t, e, 134217728, n);
    }
    qs(e, 134217728);
  }
};
Kc = function (e) {
  if (e.tag === 13) {
    var t = Vt(e),
      n = St(e, t);
    if (n !== null) {
      var r = $e();
      ot(n, e, t, r);
    }
    qs(e, t);
  }
};
Xc = function () {
  return A;
};
Zc = function (e, t) {
  var n = A;
  try {
    return (A = e), t();
  } finally {
    A = n;
  }
};
vl = function (e, t, n) {
  switch (t) {
    case "input":
      if ((cl(e, n), (t = n.name), n.type === "radio" && t != null)) {
        for (n = e; n.parentNode; ) n = n.parentNode;
        for (
          n = n.querySelectorAll(
            "input[name=" + JSON.stringify("" + t) + '][type="radio"]'
          ),
            t = 0;
          t < n.length;
          t++
        ) {
          var r = n[t];
          if (r !== e && r.form === e.form) {
            var o = ni(r);
            if (!o) throw Error(P(90));
            Pc(r), cl(r, o);
          }
        }
      }
      break;
    case "textarea":
      Tc(e, n);
      break;
    case "select":
      (t = n.value), t != null && Nn(e, !!n.multiple, t, !1);
  }
};
Mc = Ys;
Dc = on;
var Wh = { usingClientEntryPoint: !1, Events: [Br, wn, ni, Oc, Fc, Ys] },
  qn = {
    findFiberByHostInstance: Kt,
    bundleType: 0,
    version: "18.3.1",
    rendererPackageName: "react-dom",
  },
  Uh = {
    bundleType: qn.bundleType,
    version: qn.version,
    rendererPackageName: qn.rendererPackageName,
    rendererConfig: qn.rendererConfig,
    overrideHookState: null,
    overrideHookStateDeletePath: null,
    overrideHookStateRenamePath: null,
    overrideProps: null,
    overridePropsDeletePath: null,
    overridePropsRenamePath: null,
    setErrorHandler: null,
    setSuspenseHandler: null,
    scheduleUpdate: null,
    currentDispatcherRef: xt.ReactCurrentDispatcher,
    findHostInstanceByFiber: function (e) {
      return (e = Bc(e)), e === null ? null : e.stateNode;
    },
    findFiberByHostInstance: qn.findFiberByHostInstance || Ah,
    findHostInstancesForRefresh: null,
    scheduleRefresh: null,
    scheduleRoot: null,
    setRefreshHandler: null,
    getCurrentFiber: null,
    reconcilerVersion: "18.3.1-next-f1338f8080-20240426",
  };
if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
  var ao = __REACT_DEVTOOLS_GLOBAL_HOOK__;
  if (!ao.isDisabled && ao.supportsFiber)
    try {
      (Jo = ao.inject(Uh)), (ct = ao);
    } catch {}
}
Ae.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = Wh;
Ae.createPortal = function (e, t) {
  var n = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
  if (!ta(t)) throw Error(P(200));
  return Vh(e, t, null, n);
};
Ae.createRoot = function (e, t) {
  if (!ta(e)) throw Error(P(299));
  var n = !1,
    r = "",
    o = Sd;
  return (
    t != null &&
      (t.unstable_strictMode === !0 && (n = !0),
      t.identifierPrefix !== void 0 && (r = t.identifierPrefix),
      t.onRecoverableError !== void 0 && (o = t.onRecoverableError)),
    (t = Js(e, 1, !1, null, null, n, !1, r, o)),
    (e[wt] = t.current),
    $r(e.nodeType === 8 ? e.parentNode : e),
    new ea(t)
  );
};
Ae.findDOMNode = function (e) {
  if (e == null) return null;
  if (e.nodeType === 1) return e;
  var t = e._reactInternals;
  if (t === void 0)
    throw typeof e.render == "function"
      ? Error(P(188))
      : ((e = Object.keys(e).join(",")), Error(P(268, e)));
  return (e = Bc(t)), (e = e === null ? null : e.stateNode), e;
};
Ae.flushSync = function (e) {
  return on(e);
};
Ae.hydrate = function (e, t, n) {
  if (!fi(t)) throw Error(P(200));
  return di(null, e, t, !0, n);
};
Ae.hydrateRoot = function (e, t, n) {
  if (!ta(e)) throw Error(P(405));
  var r = (n != null && n.hydratedSources) || null,
    o = !1,
    i = "",
    l = Sd;
  if (
    (n != null &&
      (n.unstable_strictMode === !0 && (o = !0),
      n.identifierPrefix !== void 0 && (i = n.identifierPrefix),
      n.onRecoverableError !== void 0 && (l = n.onRecoverableError)),
    (t = wd(t, null, e, 1, n ?? null, o, !1, i, l)),
    (e[wt] = t.current),
    $r(e),
    r)
  )
    for (e = 0; e < r.length; e++)
      (n = r[e]),
        (o = n._getVersion),
        (o = o(n._source)),
        t.mutableSourceEagerHydrationData == null
          ? (t.mutableSourceEagerHydrationData = [n, o])
          : t.mutableSourceEagerHydrationData.push(n, o);
  return new ci(t);
};
Ae.render = function (e, t, n) {
  if (!fi(t)) throw Error(P(200));
  return di(null, e, t, !1, n);
};
Ae.unmountComponentAtNode = function (e) {
  if (!fi(e)) throw Error(P(40));
  return e._reactRootContainer
    ? (on(function () {
        di(null, null, e, !1, function () {
          (e._reactRootContainer = null), (e[wt] = null);
        });
      }),
      !0)
    : !1;
};
Ae.unstable_batchedUpdates = Ys;
Ae.unstable_renderSubtreeIntoContainer = function (e, t, n, r) {
  if (!fi(n)) throw Error(P(200));
  if (e == null || e._reactInternals === void 0) throw Error(P(38));
  return di(e, t, n, !1, r);
};
Ae.version = "18.3.1-next-f1338f8080-20240426";
function kd() {
  if (
    !(
      typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" ||
      typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function"
    )
  )
    try {
      __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(kd);
    } catch (e) {
      console.error(e);
    }
}
kd(), (Sc.exports = Ae);
var xd = Sc.exports;
const Hh = ss(xd);
var Cd,
  zu = xd;
(Cd = zu.createRoot), zu.hydrateRoot;
function ke(e) {
  return Object.keys(e);
}
function Xi(e) {
  return e && typeof e == "object" && !Array.isArray(e);
}
function na(e, t) {
  const n = { ...e },
    r = t;
  return (
    Xi(e) &&
      Xi(t) &&
      Object.keys(t).forEach((o) => {
        Xi(r[o]) && o in e ? (n[o] = na(n[o], r[o])) : (n[o] = r[o]);
      }),
    n
  );
}
function bh(e) {
  return e.replace(/[A-Z]/g, (t) => `-${t.toLowerCase()}`);
}
function Qh(e) {
  var t;
  return typeof e != "string" || !e.includes("var(--mantine-scale)")
    ? e
    : (t = e.match(/^calc\((.*?)\)$/)) == null
    ? void 0
    : t[1].split("*")[0].trim();
}
function Xl(e) {
  const t = Qh(e);
  return typeof t == "number"
    ? t
    : typeof t == "string"
    ? t.includes("calc") || t.includes("var")
      ? t
      : t.includes("px")
      ? Number(t.replace("px", ""))
      : t.includes("rem")
      ? Number(t.replace("rem", "")) * 16
      : t.includes("em")
      ? Number(t.replace("em", "")) * 16
      : Number(t)
    : NaN;
}
function Zi(e) {
  return e === "0rem" ? "0rem" : `calc(${e} * var(--mantine-scale))`;
}
function Ed(e, { shouldScale: t = !1 } = {}) {
  function n(r) {
    if (r === 0 || r === "0") return `0${e}`;
    if (typeof r == "number") {
      const o = `${r / 16}${e}`;
      return t ? Zi(o) : o;
    }
    if (typeof r == "string") {
      if (
        r === "" ||
        r.startsWith("calc(") ||
        r.startsWith("clamp(") ||
        r.includes("rgba(")
      )
        return r;
      if (r.includes(","))
        return r
          .split(",")
          .map((i) => n(i))
          .join(",");
      if (r.includes(" "))
        return r
          .split(" ")
          .map((i) => n(i))
          .join(" ");
      if (r.includes(e)) return t ? Zi(r) : r;
      const o = r.replace("px", "");
      if (!Number.isNaN(Number(o))) {
        const i = `${Number(o) / 16}${e}`;
        return t ? Zi(i) : i;
      }
    }
    return r;
  }
  return n;
}
const $ = Ed("rem", { shouldScale: !0 }),
  Lu = Ed("em");
function Ur(e) {
  return Object.keys(e).reduce(
    (t, n) => (e[n] !== void 0 && (t[n] = e[n]), t),
    {}
  );
}
function _d(e) {
  if (typeof e == "number") return !0;
  if (typeof e == "string") {
    if (
      e.startsWith("calc(") ||
      e.startsWith("var(") ||
      (e.includes(" ") && e.trim() !== "")
    )
      return !0;
    const t =
      /^[+-]?[0-9]+(\.[0-9]+)?(px|em|rem|ex|ch|lh|rlh|vw|vh|vmin|vmax|vb|vi|svw|svh|lvw|lvh|dvw|dvh|cm|mm|in|pt|pc|q|cqw|cqh|cqi|cqb|cqmin|cqmax|%)?$/;
    return e
      .trim()
      .split(/\s+/)
      .every((r) => t.test(r));
  }
  return !1;
}
function Gh(e) {
  const t = x.createContext(null);
  return [
    ({ children: o, value: i }) => k.jsx(t.Provider, { value: i, children: o }),
    () => {
      const o = x.useContext(t);
      if (o === null) throw new Error(e);
      return o;
    },
  ];
}
function $d(e = null) {
  const t = x.createContext(e);
  return [
    ({ children: o, value: i }) => k.jsx(t.Provider, { value: i, children: o }),
    () => x.useContext(t),
  ];
}
function Ye(e, t = "size", n = !0) {
  if (e !== void 0) return _d(e) ? (n ? $(e) : e) : `var(--${t}-${e})`;
}
function Or(e) {
  return Ye(e, "mantine-spacing");
}
function Hr(e) {
  return e === void 0
    ? "var(--mantine-radius-default)"
    : Ye(e, "mantine-radius");
}
function it(e) {
  return Ye(e, "mantine-font-size");
}
function Yh(e) {
  return Ye(e, "mantine-line-height", !1);
}
function Kh(e, t) {
  return e in t ? Xl(t[e]) : Xl(e);
}
function Nd(e, t) {
  const n = e.map((r) => ({ value: r, px: Kh(r, t) }));
  return n.sort((r, o) => r.px - o.px), n;
}
function ar(e) {
  return typeof e == "object" && e !== null
    ? "base" in e
      ? e.base
      : void 0
    : e;
}
function Xh() {
  return `mantine-${Math.random().toString(36).slice(2, 11)}`;
}
function Zh(e, t) {
  try {
    return (
      e.addEventListener("change", t), () => e.removeEventListener("change", t)
    );
  } catch {
    return e.addListener(t), () => e.removeListener(t);
  }
}
function Jh(e, t) {
  return typeof window < "u" && "matchMedia" in window
    ? window.matchMedia(e).matches
    : !1;
}
function qh(
  e,
  t,
  { getInitialValueInEffect: n } = { getInitialValueInEffect: !0 }
) {
  const [r, o] = x.useState(n ? t : Jh(e)),
    i = x.useRef();
  return (
    x.useEffect(() => {
      if ("matchMedia" in window)
        return (
          (i.current = window.matchMedia(e)),
          o(i.current.matches),
          Zh(i.current, (l) => o(l.matches))
        );
    }, [e]),
    r
  );
}
const ra = typeof document < "u" ? x.useLayoutEffect : x.useEffect;
function ey(e, t) {
  const n = x.useRef(!1);
  x.useEffect(
    () => () => {
      n.current = !1;
    },
    []
  ),
    x.useEffect(() => {
      if (n.current) return e();
      n.current = !0;
    }, t);
}
const ty = Lp.useId || (() => {});
function ny() {
  const e = ty();
  return e ? `mantine-${e.replace(/:/g, "")}` : "";
}
function Pd(e) {
  const t = ny(),
    [n, r] = x.useState(t);
  return (
    ra(() => {
      r(Xh());
    }, []),
    typeof e == "string" ? e : typeof window > "u" ? t : n
  );
}
function ry({
  value: e,
  defaultValue: t,
  finalValue: n,
  onChange: r = () => {},
}) {
  const [o, i] = x.useState(t !== void 0 ? t : n),
    l = (s, ...a) => {
      i(s), r == null || r(s, ...a);
    };
  return e !== void 0 ? [e, r, !0] : [o, l, !1];
}
function oy(e, t) {
  return qh("(prefers-reduced-motion: reduce)", e, t);
}
var iy = {};
function ly() {
  return typeof process < "u" && iy ? "production" : "development";
}
function jd(e) {
  var t,
    n,
    r = "";
  if (typeof e == "string" || typeof e == "number") r += e;
  else if (typeof e == "object")
    if (Array.isArray(e)) {
      var o = e.length;
      for (t = 0; t < o; t++)
        e[t] && (n = jd(e[t])) && (r && (r += " "), (r += n));
    } else for (n in e) e[n] && (r && (r += " "), (r += n));
  return r;
}
function Ct() {
  for (var e, t, n = 0, r = "", o = arguments.length; n < o; n++)
    (e = arguments[n]) && (t = jd(e)) && (r && (r += " "), (r += t));
  return r;
}
const sy = {};
function ay(e) {
  const t = {};
  return (
    e.forEach((n) => {
      Object.entries(n).forEach(([r, o]) => {
        t[r] ? (t[r] = Ct(t[r], o)) : (t[r] = o);
      });
    }),
    t
  );
}
function oa({ theme: e, classNames: t, props: n, stylesCtx: r }) {
  const i = (Array.isArray(t) ? t : [t]).map((l) =>
    typeof l == "function" ? l(e, n, r) : l || sy
  );
  return ay(i);
}
function Zl({ theme: e, styles: t, props: n, stylesCtx: r }) {
  return (Array.isArray(t) ? t : [t]).reduce(
    (i, l) =>
      typeof l == "function" ? { ...i, ...l(e, n, r) } : { ...i, ...l },
    {}
  );
}
const Td = x.createContext(null);
function an() {
  const e = x.useContext(Td);
  if (!e)
    throw new Error("[@mantine/core] MantineProvider was not found in tree");
  return e;
}
function uy() {
  return an().cssVariablesResolver;
}
function cy() {
  return an().classNamesPrefix;
}
function ia() {
  return an().getStyleNonce;
}
function fy() {
  return an().withStaticClasses;
}
function dy() {
  return an().headless;
}
function py() {
  var e;
  return (e = an().stylesTransform) == null ? void 0 : e.sx;
}
function my() {
  var e;
  return (e = an().stylesTransform) == null ? void 0 : e.styles;
}
function hy(e) {
  return /^#?([0-9A-F]{3}){1,2}([0-9A-F]{2})?$/i.test(e);
}
function yy(e) {
  let t = e.replace("#", "");
  if (t.length === 3) {
    const l = t.split("");
    t = [l[0], l[0], l[1], l[1], l[2], l[2]].join("");
  }
  if (t.length === 8) {
    const l = parseInt(t.slice(6, 8), 16) / 255;
    return {
      r: parseInt(t.slice(0, 2), 16),
      g: parseInt(t.slice(2, 4), 16),
      b: parseInt(t.slice(4, 6), 16),
      a: l,
    };
  }
  const n = parseInt(t, 16),
    r = (n >> 16) & 255,
    o = (n >> 8) & 255,
    i = n & 255;
  return { r, g: o, b: i, a: 1 };
}
function vy(e) {
  const [t, n, r, o] = e
    .replace(/[^0-9,./]/g, "")
    .split(/[/,]/)
    .map(Number);
  return { r: t, g: n, b: r, a: o || 1 };
}
function gy(e) {
  const t =
      /^hsla?\(\s*(\d+)\s*,\s*(\d+%)\s*,\s*(\d+%)\s*(,\s*(0?\.\d+|\d+(\.\d+)?))?\s*\)$/i,
    n = e.match(t);
  if (!n) return { r: 0, g: 0, b: 0, a: 1 };
  const r = parseInt(n[1], 10),
    o = parseInt(n[2], 10) / 100,
    i = parseInt(n[3], 10) / 100,
    l = n[5] ? parseFloat(n[5]) : void 0,
    s = (1 - Math.abs(2 * i - 1)) * o,
    a = r / 60,
    u = s * (1 - Math.abs((a % 2) - 1)),
    f = i - s / 2;
  let d, h, g;
  return (
    a >= 0 && a < 1
      ? ((d = s), (h = u), (g = 0))
      : a >= 1 && a < 2
      ? ((d = u), (h = s), (g = 0))
      : a >= 2 && a < 3
      ? ((d = 0), (h = s), (g = u))
      : a >= 3 && a < 4
      ? ((d = 0), (h = u), (g = s))
      : a >= 4 && a < 5
      ? ((d = u), (h = 0), (g = s))
      : ((d = s), (h = 0), (g = u)),
    {
      r: Math.round((d + f) * 255),
      g: Math.round((h + f) * 255),
      b: Math.round((g + f) * 255),
      a: l || 1,
    }
  );
}
function la(e) {
  return hy(e)
    ? yy(e)
    : e.startsWith("rgb")
    ? vy(e)
    : e.startsWith("hsl")
    ? gy(e)
    : { r: 0, g: 0, b: 0, a: 1 };
}
function uo(e, t) {
  if (e.startsWith("var("))
    return `color-mix(in srgb, ${e}, black ${t * 100}%)`;
  const { r: n, g: r, b: o, a: i } = la(e),
    l = 1 - t,
    s = (a) => Math.round(a * l);
  return `rgba(${s(n)}, ${s(r)}, ${s(o)}, ${i})`;
}
function Fr(e, t) {
  return typeof e.primaryShade == "number"
    ? e.primaryShade
    : t === "dark"
    ? e.primaryShade.dark
    : e.primaryShade.light;
}
function Ji(e) {
  return e <= 0.03928 ? e / 12.92 : ((e + 0.055) / 1.055) ** 2.4;
}
function wy(e) {
  const t = e.match(/oklch\((.*?)%\s/);
  return t ? parseFloat(t[1]) : null;
}
function Sy(e) {
  if (e.startsWith("oklch(")) return (wy(e) || 0) / 100;
  const { r: t, g: n, b: r } = la(e),
    o = t / 255,
    i = n / 255,
    l = r / 255,
    s = Ji(o),
    a = Ji(i),
    u = Ji(l);
  return 0.2126 * s + 0.7152 * a + 0.0722 * u;
}
function er(e, t = 0.179) {
  return e.startsWith("var(") ? !1 : Sy(e) > t;
}
function un({ color: e, theme: t, colorScheme: n }) {
  if (typeof e != "string")
    throw new Error(
      `[@mantine/core] Failed to parse color. Expected color to be a string, instead got ${typeof e}`
    );
  if (e === "bright")
    return {
      color: e,
      value: n === "dark" ? t.white : t.black,
      shade: void 0,
      isThemeColor: !1,
      isLight: er(n === "dark" ? t.white : t.black, t.luminanceThreshold),
      variable: "--mantine-color-bright",
    };
  if (e === "dimmed")
    return {
      color: e,
      value: n === "dark" ? t.colors.dark[2] : t.colors.gray[7],
      shade: void 0,
      isThemeColor: !1,
      isLight: er(
        n === "dark" ? t.colors.dark[2] : t.colors.gray[6],
        t.luminanceThreshold
      ),
      variable: "--mantine-color-dimmed",
    };
  if (e === "white" || e === "black")
    return {
      color: e,
      value: e === "white" ? t.white : t.black,
      shade: void 0,
      isThemeColor: !1,
      isLight: er(e === "white" ? t.white : t.black, t.luminanceThreshold),
      variable: `--mantine-color-${e}`,
    };
  const [r, o] = e.split("."),
    i = o ? Number(o) : void 0,
    l = r in t.colors;
  if (l) {
    const s = i !== void 0 ? t.colors[r][i] : t.colors[r][Fr(t, n || "light")];
    return {
      color: r,
      value: s,
      shade: i,
      isThemeColor: l,
      isLight: er(s, t.luminanceThreshold),
      variable: o ? `--mantine-color-${r}-${i}` : `--mantine-color-${r}-filled`,
    };
  }
  return {
    color: e,
    value: e,
    isThemeColor: l,
    isLight: er(e, t.luminanceThreshold),
    shade: i,
    variable: void 0,
  };
}
function Ut(e, t) {
  const n = un({ color: e || t.primaryColor, theme: t });
  return n.variable ? `var(${n.variable})` : e;
}
function Jl(e, t) {
  const n = {
      from: (e == null ? void 0 : e.from) || t.defaultGradient.from,
      to: (e == null ? void 0 : e.to) || t.defaultGradient.to,
      deg: (e == null ? void 0 : e.deg) || t.defaultGradient.deg || 0,
    },
    r = Ut(n.from, t),
    o = Ut(n.to, t);
  return `linear-gradient(${n.deg}deg, ${r} 0%, ${o} 100%)`;
}
function dt(e, t) {
  if (typeof e != "string" || t > 1 || t < 0) return "rgba(0, 0, 0, 1)";
  if (e.startsWith("var(")) {
    const i = (1 - t) * 100;
    return `color-mix(in srgb, ${e}, transparent ${i}%)`;
  }
  if (e.startsWith("oklch"))
    return e.includes("/")
      ? e.replace(/\/\s*[\d.]+\s*\)/, `/ ${t})`)
      : e.replace(")", ` / ${t})`);
  const { r: n, g: r, b: o } = la(e);
  return `rgba(${n}, ${r}, ${o}, ${t})`;
}
const fn = dt,
  ky = ({ color: e, theme: t, variant: n, gradient: r, autoContrast: o }) => {
    const i = un({ color: e, theme: t }),
      l = typeof o == "boolean" ? o : t.autoContrast;
    if (n === "filled") {
      const s =
        l && i.isLight
          ? "var(--mantine-color-black)"
          : "var(--mantine-color-white)";
      return i.isThemeColor
        ? i.shade === void 0
          ? {
              background: `var(--mantine-color-${e}-filled)`,
              hover: `var(--mantine-color-${e}-filled-hover)`,
              color: s,
              border: `${$(1)} solid transparent`,
            }
          : {
              background: `var(--mantine-color-${i.color}-${i.shade})`,
              hover: `var(--mantine-color-${i.color}-${
                i.shade === 9 ? 8 : i.shade + 1
              })`,
              color: s,
              border: `${$(1)} solid transparent`,
            }
        : {
            background: e,
            hover: uo(e, 0.1),
            color: s,
            border: `${$(1)} solid transparent`,
          };
    }
    if (n === "light") {
      if (i.isThemeColor) {
        if (i.shade === void 0)
          return {
            background: `var(--mantine-color-${e}-light)`,
            hover: `var(--mantine-color-${e}-light-hover)`,
            color: `var(--mantine-color-${e}-light-color)`,
            border: `${$(1)} solid transparent`,
          };
        const s = t.colors[i.color][i.shade];
        return {
          background: dt(s, 0.1),
          hover: dt(s, 0.12),
          color: `var(--mantine-color-${i.color}-${Math.min(i.shade, 6)})`,
          border: `${$(1)} solid transparent`,
        };
      }
      return {
        background: dt(e, 0.1),
        hover: dt(e, 0.12),
        color: e,
        border: `${$(1)} solid transparent`,
      };
    }
    if (n === "outline")
      return i.isThemeColor
        ? i.shade === void 0
          ? {
              background: "transparent",
              hover: `var(--mantine-color-${e}-outline-hover)`,
              color: `var(--mantine-color-${e}-outline)`,
              border: `${$(1)} solid var(--mantine-color-${e}-outline)`,
            }
          : {
              background: "transparent",
              hover: dt(t.colors[i.color][i.shade], 0.05),
              color: `var(--mantine-color-${i.color}-${i.shade})`,
              border: `${$(1)} solid var(--mantine-color-${i.color}-${
                i.shade
              })`,
            }
        : {
            background: "transparent",
            hover: dt(e, 0.05),
            color: e,
            border: `${$(1)} solid ${e}`,
          };
    if (n === "subtle") {
      if (i.isThemeColor) {
        if (i.shade === void 0)
          return {
            background: "transparent",
            hover: `var(--mantine-color-${e}-light-hover)`,
            color: `var(--mantine-color-${e}-light-color)`,
            border: `${$(1)} solid transparent`,
          };
        const s = t.colors[i.color][i.shade];
        return {
          background: "transparent",
          hover: dt(s, 0.12),
          color: `var(--mantine-color-${i.color}-${Math.min(i.shade, 6)})`,
          border: `${$(1)} solid transparent`,
        };
      }
      return {
        background: "transparent",
        hover: dt(e, 0.12),
        color: e,
        border: `${$(1)} solid transparent`,
      };
    }
    return n === "transparent"
      ? i.isThemeColor
        ? i.shade === void 0
          ? {
              background: "transparent",
              hover: "transparent",
              color: `var(--mantine-color-${e}-light-color)`,
              border: `${$(1)} solid transparent`,
            }
          : {
              background: "transparent",
              hover: "transparent",
              color: `var(--mantine-color-${i.color}-${Math.min(i.shade, 6)})`,
              border: `${$(1)} solid transparent`,
            }
        : {
            background: "transparent",
            hover: "transparent",
            color: e,
            border: `${$(1)} solid transparent`,
          }
      : n === "white"
      ? i.isThemeColor
        ? i.shade === void 0
          ? {
              background: "var(--mantine-color-white)",
              hover: uo(t.white, 0.01),
              color: `var(--mantine-color-${e}-filled)`,
              border: `${$(1)} solid transparent`,
            }
          : {
              background: "var(--mantine-color-white)",
              hover: uo(t.white, 0.01),
              color: `var(--mantine-color-${i.color}-${i.shade})`,
              border: `${$(1)} solid transparent`,
            }
        : {
            background: "var(--mantine-color-white)",
            hover: uo(t.white, 0.01),
            color: e,
            border: `${$(1)} solid transparent`,
          }
      : n === "gradient"
      ? {
          background: Jl(r, t),
          hover: Jl(r, t),
          color: "var(--mantine-color-white)",
          border: "none",
        }
      : n === "default"
      ? {
          background: "var(--mantine-color-default)",
          hover: "var(--mantine-color-default-hover)",
          color: "var(--mantine-color-default-color)",
          border: `${$(1)} solid var(--mantine-color-default-border)`,
        }
      : {};
  },
  xy = {
    dark: [
      "#C9C9C9",
      "#b8b8b8",
      "#828282",
      "#696969",
      "#424242",
      "#3b3b3b",
      "#2e2e2e",
      "#242424",
      "#1f1f1f",
      "#141414",
    ],
    gray: [
      "#f8f9fa",
      "#f1f3f5",
      "#e9ecef",
      "#dee2e6",
      "#ced4da",
      "#adb5bd",
      "#868e96",
      "#495057",
      "#343a40",
      "#212529",
    ],
    red: [
      "#fff5f5",
      "#ffe3e3",
      "#ffc9c9",
      "#ffa8a8",
      "#ff8787",
      "#ff6b6b",
      "#fa5252",
      "#f03e3e",
      "#e03131",
      "#c92a2a",
    ],
    pink: [
      "#fff0f6",
      "#ffdeeb",
      "#fcc2d7",
      "#faa2c1",
      "#f783ac",
      "#f06595",
      "#e64980",
      "#d6336c",
      "#c2255c",
      "#a61e4d",
    ],
    grape: [
      "#f8f0fc",
      "#f3d9fa",
      "#eebefa",
      "#e599f7",
      "#da77f2",
      "#cc5de8",
      "#be4bdb",
      "#ae3ec9",
      "#9c36b5",
      "#862e9c",
    ],
    violet: [
      "#f3f0ff",
      "#e5dbff",
      "#d0bfff",
      "#b197fc",
      "#9775fa",
      "#845ef7",
      "#7950f2",
      "#7048e8",
      "#6741d9",
      "#5f3dc4",
    ],
    indigo: [
      "#edf2ff",
      "#dbe4ff",
      "#bac8ff",
      "#91a7ff",
      "#748ffc",
      "#5c7cfa",
      "#4c6ef5",
      "#4263eb",
      "#3b5bdb",
      "#364fc7",
    ],
    blue: [
      "#e7f5ff",
      "#d0ebff",
      "#a5d8ff",
      "#74c0fc",
      "#4dabf7",
      "#339af0",
      "#228be6",
      "#1c7ed6",
      "#1971c2",
      "#1864ab",
    ],
    cyan: [
      "#e3fafc",
      "#c5f6fa",
      "#99e9f2",
      "#66d9e8",
      "#3bc9db",
      "#22b8cf",
      "#15aabf",
      "#1098ad",
      "#0c8599",
      "#0b7285",
    ],
    teal: [
      "#e6fcf5",
      "#c3fae8",
      "#96f2d7",
      "#63e6be",
      "#38d9a9",
      "#20c997",
      "#12b886",
      "#0ca678",
      "#099268",
      "#087f5b",
    ],
    green: [
      "#ebfbee",
      "#d3f9d8",
      "#b2f2bb",
      "#8ce99a",
      "#69db7c",
      "#51cf66",
      "#40c057",
      "#37b24d",
      "#2f9e44",
      "#2b8a3e",
    ],
    lime: [
      "#f4fce3",
      "#e9fac8",
      "#d8f5a2",
      "#c0eb75",
      "#a9e34b",
      "#94d82d",
      "#82c91e",
      "#74b816",
      "#66a80f",
      "#5c940d",
    ],
    yellow: [
      "#fff9db",
      "#fff3bf",
      "#ffec99",
      "#ffe066",
      "#ffd43b",
      "#fcc419",
      "#fab005",
      "#f59f00",
      "#f08c00",
      "#e67700",
    ],
    orange: [
      "#fff4e6",
      "#ffe8cc",
      "#ffd8a8",
      "#ffc078",
      "#ffa94d",
      "#ff922b",
      "#fd7e14",
      "#f76707",
      "#e8590c",
      "#d9480f",
    ],
  },
  Iu =
    "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji",
  sa = {
    scale: 1,
    fontSmoothing: !0,
    focusRing: "auto",
    white: "#fff",
    black: "#000",
    colors: xy,
    primaryShade: { light: 6, dark: 8 },
    primaryColor: "blue",
    variantColorResolver: ky,
    autoContrast: !1,
    luminanceThreshold: 0.3,
    fontFamily: Iu,
    fontFamilyMonospace:
      "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace",
    respectReducedMotion: !1,
    cursorType: "default",
    defaultGradient: { from: "blue", to: "cyan", deg: 45 },
    defaultRadius: "sm",
    activeClassName: "mantine-active",
    focusClassName: "",
    headings: {
      fontFamily: Iu,
      fontWeight: "700",
      textWrap: "wrap",
      sizes: {
        h1: { fontSize: $(34), lineHeight: "1.3" },
        h2: { fontSize: $(26), lineHeight: "1.35" },
        h3: { fontSize: $(22), lineHeight: "1.4" },
        h4: { fontSize: $(18), lineHeight: "1.45" },
        h5: { fontSize: $(16), lineHeight: "1.5" },
        h6: { fontSize: $(14), lineHeight: "1.5" },
      },
    },
    fontSizes: { xs: $(12), sm: $(14), md: $(16), lg: $(18), xl: $(20) },
    lineHeights: { xs: "1.4", sm: "1.45", md: "1.55", lg: "1.6", xl: "1.65" },
    radius: { xs: $(2), sm: $(4), md: $(8), lg: $(16), xl: $(32) },
    spacing: { xs: $(10), sm: $(12), md: $(16), lg: $(20), xl: $(32) },
    breakpoints: { xs: "36em", sm: "48em", md: "62em", lg: "75em", xl: "88em" },
    shadows: {
      xs: `0 ${$(1)} ${$(3)} rgba(0, 0, 0, 0.05), 0 ${$(1)} ${$(
        2
      )} rgba(0, 0, 0, 0.1)`,
      sm: `0 ${$(1)} ${$(3)} rgba(0, 0, 0, 0.05), rgba(0, 0, 0, 0.05) 0 ${$(
        10
      )} ${$(15)} ${$(-5)}, rgba(0, 0, 0, 0.04) 0 ${$(7)} ${$(7)} ${$(-5)}`,
      md: `0 ${$(1)} ${$(3)} rgba(0, 0, 0, 0.05), rgba(0, 0, 0, 0.05) 0 ${$(
        20
      )} ${$(25)} ${$(-5)}, rgba(0, 0, 0, 0.04) 0 ${$(10)} ${$(10)} ${$(-5)}`,
      lg: `0 ${$(1)} ${$(3)} rgba(0, 0, 0, 0.05), rgba(0, 0, 0, 0.05) 0 ${$(
        28
      )} ${$(23)} ${$(-7)}, rgba(0, 0, 0, 0.04) 0 ${$(12)} ${$(12)} ${$(-7)}`,
      xl: `0 ${$(1)} ${$(3)} rgba(0, 0, 0, 0.05), rgba(0, 0, 0, 0.05) 0 ${$(
        36
      )} ${$(28)} ${$(-7)}, rgba(0, 0, 0, 0.04) 0 ${$(17)} ${$(17)} ${$(-7)}`,
    },
    other: {},
    components: {},
  };
function Ou(e) {
  return e === "auto" || e === "dark" || e === "light";
}
function Cy({ key: e = "mantine-color-scheme-value" } = {}) {
  let t;
  return {
    get: (n) => {
      if (typeof window > "u") return n;
      try {
        const r = window.localStorage.getItem(e);
        return Ou(r) ? r : n;
      } catch {
        return n;
      }
    },
    set: (n) => {
      try {
        window.localStorage.setItem(e, n);
      } catch (r) {
        console.warn(
          "[@mantine/core] Local storage color scheme manager was unable to save color scheme.",
          r
        );
      }
    },
    subscribe: (n) => {
      (t = (r) => {
        r.storageArea === window.localStorage &&
          r.key === e &&
          Ou(r.newValue) &&
          n(r.newValue);
      }),
        window.addEventListener("storage", t);
    },
    unsubscribe: () => {
      window.removeEventListener("storage", t);
    },
    clear: () => {
      window.localStorage.removeItem(e);
    },
  };
}
const Ey =
    "[@mantine/core] MantineProvider: Invalid theme.primaryColor, it accepts only key of theme.colors, learn more – https://mantine.dev/theming/colors/#primary-color",
  Fu =
    "[@mantine/core] MantineProvider: Invalid theme.primaryShade, it accepts only 0-9 integers or an object { light: 0-9, dark: 0-9 }";
function qi(e) {
  return e < 0 || e > 9 ? !1 : parseInt(e.toString(), 10) === e;
}
function Mu(e) {
  if (!(e.primaryColor in e.colors)) throw new Error(Ey);
  if (
    typeof e.primaryShade == "object" &&
    (!qi(e.primaryShade.dark) || !qi(e.primaryShade.light))
  )
    throw new Error(Fu);
  if (typeof e.primaryShade == "number" && !qi(e.primaryShade))
    throw new Error(Fu);
}
function _y(e, t) {
  var r;
  if (!t) return Mu(e), e;
  const n = na(e, t);
  return (
    t.fontFamily &&
      !((r = t.headings) != null && r.fontFamily) &&
      (n.headings.fontFamily = t.fontFamily),
    Mu(n),
    n
  );
}
const aa = x.createContext(null),
  $y = () => x.useContext(aa) || sa;
function Et() {
  const e = x.useContext(aa);
  if (!e)
    throw new Error(
      "@mantine/core: MantineProvider was not found in component tree, make sure you have it in your app"
    );
  return e;
}
function Rd({ theme: e, children: t, inherit: n = !0 }) {
  const r = $y(),
    o = x.useMemo(() => _y(n ? r : sa, e), [e, r, n]);
  return k.jsx(aa.Provider, { value: o, children: t });
}
Rd.displayName = "@mantine/core/MantineThemeProvider";
function Ny() {
  const e = Et(),
    t = ia(),
    n = ke(e.breakpoints).reduce((r, o) => {
      const i = e.breakpoints[o].includes("px"),
        l = Xl(e.breakpoints[o]),
        s = i ? `${l - 0.1}px` : Lu(l - 0.1),
        a = i ? `${l}px` : Lu(l);
      return `${r}@media (max-width: ${s}) {.mantine-visible-from-${o} {display: none !important;}}@media (min-width: ${a}) {.mantine-hidden-from-${o} {display: none !important;}}`;
    }, "");
  return k.jsx("style", {
    "data-mantine-styles": "classes",
    nonce: t == null ? void 0 : t(),
    dangerouslySetInnerHTML: { __html: n },
  });
}
function el(e) {
  return Object.entries(e)
    .map(([t, n]) => `${t}: ${n};`)
    .join("");
}
function tr(e, t) {
  return (Array.isArray(e) ? e : [e]).reduce((r, o) => `${o}{${r}}`, t);
}
function Py(e, t) {
  const n = el(e.variables),
    r = n ? tr(t, n) : "",
    o = el(e.dark),
    i = el(e.light),
    l = o
      ? tr(
          t === ":host"
            ? `${t}([data-mantine-color-scheme="dark"])`
            : `${t}[data-mantine-color-scheme="dark"]`,
          o
        )
      : "",
    s = i
      ? tr(
          t === ":host"
            ? `${t}([data-mantine-color-scheme="light"])`
            : `${t}[data-mantine-color-scheme="light"]`,
          i
        )
      : "";
  return `${r}${l}${s}`;
}
function ua({ color: e, theme: t, autoContrast: n }) {
  return (typeof n == "boolean" ? n : t.autoContrast) &&
    un({ color: e || t.primaryColor, theme: t }).isLight
    ? "var(--mantine-color-black)"
    : "var(--mantine-color-white)";
}
function Du(e, t) {
  return ua({
    color: e.colors[e.primaryColor][Fr(e, t)],
    theme: e,
    autoContrast: null,
  });
}
function co({
  theme: e,
  color: t,
  colorScheme: n,
  name: r = t,
  withColorValues: o = !0,
}) {
  if (!e.colors[t]) return {};
  if (n === "light") {
    const s = Fr(e, "light"),
      a = {
        [`--mantine-color-${r}-text`]: `var(--mantine-color-${r}-filled)`,
        [`--mantine-color-${r}-filled`]: `var(--mantine-color-${r}-${s})`,
        [`--mantine-color-${r}-filled-hover`]: `var(--mantine-color-${r}-${
          s === 9 ? 8 : s + 1
        })`,
        [`--mantine-color-${r}-light`]: fn(e.colors[t][s], 0.1),
        [`--mantine-color-${r}-light-hover`]: fn(e.colors[t][s], 0.12),
        [`--mantine-color-${r}-light-color`]: `var(--mantine-color-${r}-${s})`,
        [`--mantine-color-${r}-outline`]: `var(--mantine-color-${r}-${s})`,
        [`--mantine-color-${r}-outline-hover`]: fn(e.colors[t][s], 0.05),
      };
    return o
      ? {
          [`--mantine-color-${r}-0`]: e.colors[t][0],
          [`--mantine-color-${r}-1`]: e.colors[t][1],
          [`--mantine-color-${r}-2`]: e.colors[t][2],
          [`--mantine-color-${r}-3`]: e.colors[t][3],
          [`--mantine-color-${r}-4`]: e.colors[t][4],
          [`--mantine-color-${r}-5`]: e.colors[t][5],
          [`--mantine-color-${r}-6`]: e.colors[t][6],
          [`--mantine-color-${r}-7`]: e.colors[t][7],
          [`--mantine-color-${r}-8`]: e.colors[t][8],
          [`--mantine-color-${r}-9`]: e.colors[t][9],
          ...a,
        }
      : a;
  }
  const i = Fr(e, "dark"),
    l = {
      [`--mantine-color-${r}-text`]: `var(--mantine-color-${r}-4)`,
      [`--mantine-color-${r}-filled`]: `var(--mantine-color-${r}-${i})`,
      [`--mantine-color-${r}-filled-hover`]: `var(--mantine-color-${r}-${
        i === 9 ? 8 : i + 1
      })`,
      [`--mantine-color-${r}-light`]: fn(e.colors[t][Math.max(0, i - 2)], 0.15),
      [`--mantine-color-${r}-light-hover`]: fn(
        e.colors[t][Math.max(0, i - 2)],
        0.2
      ),
      [`--mantine-color-${r}-light-color`]: `var(--mantine-color-${r}-${Math.max(
        i - 5,
        0
      )})`,
      [`--mantine-color-${r}-outline`]: `var(--mantine-color-${r}-${Math.max(
        i - 4,
        0
      )})`,
      [`--mantine-color-${r}-outline-hover`]: fn(
        e.colors[t][Math.max(i - 4, 0)],
        0.05
      ),
    };
  return o
    ? {
        [`--mantine-color-${r}-0`]: e.colors[t][0],
        [`--mantine-color-${r}-1`]: e.colors[t][1],
        [`--mantine-color-${r}-2`]: e.colors[t][2],
        [`--mantine-color-${r}-3`]: e.colors[t][3],
        [`--mantine-color-${r}-4`]: e.colors[t][4],
        [`--mantine-color-${r}-5`]: e.colors[t][5],
        [`--mantine-color-${r}-6`]: e.colors[t][6],
        [`--mantine-color-${r}-7`]: e.colors[t][7],
        [`--mantine-color-${r}-8`]: e.colors[t][8],
        [`--mantine-color-${r}-9`]: e.colors[t][9],
        ...l,
      }
    : l;
}
function jy(e) {
  return !!e && typeof e == "object" && "mantine-virtual-color" in e;
}
function dn(e, t, n) {
  ke(t).forEach((r) => Object.assign(e, { [`--mantine-${n}-${r}`]: t[r] }));
}
const zd = (e) => {
  const t = Fr(e, "light"),
    n =
      e.defaultRadius in e.radius
        ? e.radius[e.defaultRadius]
        : $(e.defaultRadius),
    r = {
      variables: {
        "--mantine-scale": e.scale.toString(),
        "--mantine-cursor-type": e.cursorType,
        "--mantine-color-scheme": "light dark",
        "--mantine-webkit-font-smoothing": e.fontSmoothing
          ? "antialiased"
          : "unset",
        "--mantine-moz-font-smoothing": e.fontSmoothing ? "grayscale" : "unset",
        "--mantine-color-white": e.white,
        "--mantine-color-black": e.black,
        "--mantine-line-height": e.lineHeights.md,
        "--mantine-font-family": e.fontFamily,
        "--mantine-font-family-monospace": e.fontFamilyMonospace,
        "--mantine-font-family-headings": e.headings.fontFamily,
        "--mantine-heading-font-weight": e.headings.fontWeight,
        "--mantine-heading-text-wrap": e.headings.textWrap,
        "--mantine-radius-default": n,
        "--mantine-primary-color-filled": `var(--mantine-color-${e.primaryColor}-filled)`,
        "--mantine-primary-color-filled-hover": `var(--mantine-color-${e.primaryColor}-filled-hover)`,
        "--mantine-primary-color-light": `var(--mantine-color-${e.primaryColor}-light)`,
        "--mantine-primary-color-light-hover": `var(--mantine-color-${e.primaryColor}-light-hover)`,
        "--mantine-primary-color-light-color": `var(--mantine-color-${e.primaryColor}-light-color)`,
      },
      light: {
        "--mantine-primary-color-contrast": Du(e, "light"),
        "--mantine-color-bright": "var(--mantine-color-black)",
        "--mantine-color-text": e.black,
        "--mantine-color-body": e.white,
        "--mantine-color-error": "var(--mantine-color-red-6)",
        "--mantine-color-placeholder": "var(--mantine-color-gray-5)",
        "--mantine-color-anchor": `var(--mantine-color-${e.primaryColor}-${t})`,
        "--mantine-color-default": "var(--mantine-color-white)",
        "--mantine-color-default-hover": "var(--mantine-color-gray-0)",
        "--mantine-color-default-color": "var(--mantine-color-black)",
        "--mantine-color-default-border": "var(--mantine-color-gray-4)",
        "--mantine-color-dimmed": "var(--mantine-color-gray-6)",
      },
      dark: {
        "--mantine-primary-color-contrast": Du(e, "dark"),
        "--mantine-color-bright": "var(--mantine-color-white)",
        "--mantine-color-text": "var(--mantine-color-dark-0)",
        "--mantine-color-body": "var(--mantine-color-dark-7)",
        "--mantine-color-error": "var(--mantine-color-red-8)",
        "--mantine-color-placeholder": "var(--mantine-color-dark-3)",
        "--mantine-color-anchor": `var(--mantine-color-${e.primaryColor}-4)`,
        "--mantine-color-default": "var(--mantine-color-dark-6)",
        "--mantine-color-default-hover": "var(--mantine-color-dark-5)",
        "--mantine-color-default-color": "var(--mantine-color-white)",
        "--mantine-color-default-border": "var(--mantine-color-dark-4)",
        "--mantine-color-dimmed": "var(--mantine-color-dark-2)",
      },
    };
  dn(r.variables, e.breakpoints, "breakpoint"),
    dn(r.variables, e.spacing, "spacing"),
    dn(r.variables, e.fontSizes, "font-size"),
    dn(r.variables, e.lineHeights, "line-height"),
    dn(r.variables, e.shadows, "shadow"),
    dn(r.variables, e.radius, "radius"),
    e.colors[e.primaryColor].forEach((i, l) => {
      r.variables[
        `--mantine-primary-color-${l}`
      ] = `var(--mantine-color-${e.primaryColor}-${l})`;
    }),
    ke(e.colors).forEach((i) => {
      const l = e.colors[i];
      if (jy(l)) {
        Object.assign(
          r.light,
          co({
            theme: e,
            name: l.name,
            color: l.light,
            colorScheme: "light",
            withColorValues: !0,
          })
        ),
          Object.assign(
            r.dark,
            co({
              theme: e,
              name: l.name,
              color: l.dark,
              colorScheme: "dark",
              withColorValues: !0,
            })
          );
        return;
      }
      l.forEach((s, a) => {
        r.variables[`--mantine-color-${i}-${a}`] = s;
      }),
        Object.assign(
          r.light,
          co({ theme: e, color: i, colorScheme: "light", withColorValues: !1 })
        ),
        Object.assign(
          r.dark,
          co({ theme: e, color: i, colorScheme: "dark", withColorValues: !1 })
        );
    });
  const o = e.headings.sizes;
  return (
    ke(o).forEach((i) => {
      (r.variables[`--mantine-${i}-font-size`] = o[i].fontSize),
        (r.variables[`--mantine-${i}-line-height`] = o[i].lineHeight),
        (r.variables[`--mantine-${i}-font-weight`] =
          o[i].fontWeight || e.headings.fontWeight);
    }),
    r
  );
};
function Ty({ theme: e, generator: t }) {
  const n = zd(e),
    r = t == null ? void 0 : t(e);
  return r ? na(n, r) : n;
}
const tl = zd(sa);
function Ry(e) {
  const t = { variables: {}, light: {}, dark: {} };
  return (
    ke(e.variables).forEach((n) => {
      tl.variables[n] !== e.variables[n] && (t.variables[n] = e.variables[n]);
    }),
    ke(e.light).forEach((n) => {
      tl.light[n] !== e.light[n] && (t.light[n] = e.light[n]);
    }),
    ke(e.dark).forEach((n) => {
      tl.dark[n] !== e.dark[n] && (t.dark[n] = e.dark[n]);
    }),
    t
  );
}
function zy(e) {
  return `
  ${e}[data-mantine-color-scheme="dark"] { --mantine-color-scheme: dark; }
  ${e}[data-mantine-color-scheme="light"] { --mantine-color-scheme: light; }
`;
}
function Ld({ cssVariablesSelector: e, deduplicateCssVariables: t }) {
  const n = Et(),
    r = ia(),
    o = uy(),
    i = Ty({ theme: n, generator: o }),
    l = e === ":root" && t,
    s = l ? Ry(i) : i,
    a = Py(s, e);
  return a
    ? k.jsx("style", {
        "data-mantine-styles": !0,
        nonce: r == null ? void 0 : r(),
        dangerouslySetInnerHTML: { __html: `${a}${l ? "" : zy(e)}` },
      })
    : null;
}
Ld.displayName = "@mantine/CssVariables";
function Ly() {
  const e = console.error;
  console.error = (...t) => {
    (t.length > 1 &&
      typeof t[0] == "string" &&
      t[0].toLowerCase().includes("extra attributes from the server") &&
      typeof t[1] == "string" &&
      t[1].toLowerCase().includes("data-mantine-color-scheme")) ||
      e(...t);
  };
}
function pn(e, t) {
  var r;
  const n =
    e !== "auto"
      ? e
      : window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  (r = t()) == null || r.setAttribute("data-mantine-color-scheme", n);
}
function Iy({
  manager: e,
  defaultColorScheme: t,
  getRootElement: n,
  forceColorScheme: r,
}) {
  const o = x.useRef(),
    [i, l] = x.useState(() => e.get(t)),
    s = r || i,
    a = x.useCallback(
      (f) => {
        r || (pn(f, n), l(f), e.set(f));
      },
      [e.set, s, r]
    ),
    u = x.useCallback(() => {
      l(t), pn(t, n), e.clear();
    }, [e.clear, t]);
  return (
    x.useEffect(
      () => (e.subscribe(a), e.unsubscribe),
      [e.subscribe, e.unsubscribe]
    ),
    ra(() => {
      pn(e.get(t), n);
    }, []),
    x.useEffect(() => {
      var d;
      if (r) return pn(r, n), () => {};
      r === void 0 && pn(i, n),
        (o.current = window.matchMedia("(prefers-color-scheme: dark)"));
      const f = (h) => {
        i === "auto" && pn(h.matches ? "dark" : "light", n);
      };
      return (
        (d = o.current) == null || d.addEventListener("change", f),
        () => {
          var h;
          return (h = o.current) == null
            ? void 0
            : h.removeEventListener("change", f);
        }
      );
    }, [i, r]),
    { colorScheme: s, setColorScheme: a, clearColorScheme: u }
  );
}
function Oy({ respectReducedMotion: e, getRootElement: t }) {
  ra(() => {
    var n;
    e &&
      ((n = t()) == null ||
        n.setAttribute("data-respect-reduced-motion", "true"));
  }, [e]);
}
Ly();
function Id({
  theme: e,
  children: t,
  getStyleNonce: n,
  withStaticClasses: r = !0,
  withGlobalClasses: o = !0,
  deduplicateCssVariables: i = !0,
  withCssVariables: l = !0,
  cssVariablesSelector: s = ":root",
  classNamesPrefix: a = "mantine",
  colorSchemeManager: u = Cy(),
  defaultColorScheme: f = "light",
  getRootElement: d = () => document.documentElement,
  cssVariablesResolver: h,
  forceColorScheme: g,
  stylesTransform: y,
}) {
  const {
    colorScheme: v,
    setColorScheme: C,
    clearColorScheme: m,
  } = Iy({
    defaultColorScheme: f,
    forceColorScheme: g,
    manager: u,
    getRootElement: d,
  });
  return (
    Oy({
      respectReducedMotion: (e == null ? void 0 : e.respectReducedMotion) || !1,
      getRootElement: d,
    }),
    k.jsx(Td.Provider, {
      value: {
        colorScheme: v,
        setColorScheme: C,
        clearColorScheme: m,
        getRootElement: d,
        classNamesPrefix: a,
        getStyleNonce: n,
        cssVariablesResolver: h,
        cssVariablesSelector: s,
        withStaticClasses: r,
        stylesTransform: y,
      },
      children: k.jsxs(Rd, {
        theme: e,
        children: [
          l &&
            k.jsx(Ld, { cssVariablesSelector: s, deduplicateCssVariables: i }),
          o && k.jsx(Ny, {}),
          t,
        ],
      }),
    })
  );
}
Id.displayName = "@mantine/core/MantineProvider";
const Fy = {
  always: "mantine-focus-always",
  auto: "mantine-focus-auto",
  never: "mantine-focus-never",
};
function My({ theme: e, options: t, unstyled: n }) {
  return Ct(
    (t == null ? void 0 : t.focusable) &&
      !n &&
      (e.focusClassName || Fy[e.focusRing]),
    (t == null ? void 0 : t.active) && !n && e.activeClassName
  );
}
function Dy({ selector: e, stylesCtx: t, options: n, props: r, theme: o }) {
  return oa({
    theme: o,
    classNames: n == null ? void 0 : n.classNames,
    props: (n == null ? void 0 : n.props) || r,
    stylesCtx: t,
  })[e];
}
function Vu({ selector: e, stylesCtx: t, theme: n, classNames: r, props: o }) {
  return oa({ theme: n, classNames: r, props: o, stylesCtx: t })[e];
}
function Vy({ rootSelector: e, selector: t, className: n }) {
  return e === t ? n : void 0;
}
function Ay({ selector: e, classes: t, unstyled: n }) {
  return n ? void 0 : t[e];
}
function By({
  themeName: e,
  classNamesPrefix: t,
  selector: n,
  withStaticClass: r,
}) {
  return r === !1 ? [] : e.map((o) => `${t}-${o}-${n}`);
}
function Wy({ themeName: e, theme: t, selector: n, props: r, stylesCtx: o }) {
  return e.map((i) => {
    var l, s;
    return (s = oa({
      theme: t,
      classNames: (l = t.components[i]) == null ? void 0 : l.classNames,
      props: r,
      stylesCtx: o,
    })) == null
      ? void 0
      : s[n];
  });
}
function Uy({ options: e, classes: t, selector: n, unstyled: r }) {
  return e != null && e.variant && !r ? t[`${n}--${e.variant}`] : void 0;
}
function Hy({
  theme: e,
  options: t,
  themeName: n,
  selector: r,
  classNamesPrefix: o,
  classNames: i,
  classes: l,
  unstyled: s,
  className: a,
  rootSelector: u,
  props: f,
  stylesCtx: d,
  withStaticClasses: h,
  headless: g,
  transformedStyles: y,
}) {
  return Ct(
    My({ theme: e, options: t, unstyled: s || g }),
    Wy({ theme: e, themeName: n, selector: r, props: f, stylesCtx: d }),
    Uy({ options: t, classes: l, selector: r, unstyled: s }),
    Vu({ selector: r, stylesCtx: d, theme: e, classNames: i, props: f }),
    Vu({ selector: r, stylesCtx: d, theme: e, classNames: y, props: f }),
    Dy({ selector: r, stylesCtx: d, options: t, props: f, theme: e }),
    Vy({ rootSelector: u, selector: r, className: a }),
    Ay({ selector: r, classes: l, unstyled: s || g }),
    h &&
      !g &&
      By({
        themeName: n,
        classNamesPrefix: o,
        selector: r,
        withStaticClass: t == null ? void 0 : t.withStaticClass,
      }),
    t == null ? void 0 : t.className
  );
}
function by({ theme: e, themeName: t, props: n, stylesCtx: r, selector: o }) {
  return t
    .map((i) => {
      var l;
      return Zl({
        theme: e,
        styles: (l = e.components[i]) == null ? void 0 : l.styles,
        props: n,
        stylesCtx: r,
      })[o];
    })
    .reduce((i, l) => ({ ...i, ...l }), {});
}
function ql({ style: e, theme: t }) {
  return Array.isArray(e)
    ? [...e].reduce((n, r) => ({ ...n, ...ql({ style: r, theme: t }) }), {})
    : typeof e == "function"
    ? e(t)
    : e ?? {};
}
function Qy(e) {
  return e.reduce(
    (t, n) => (
      n &&
        Object.keys(n).forEach((r) => {
          t[r] = { ...t[r], ...Ur(n[r]) };
        }),
      t
    ),
    {}
  );
}
function Gy({
  vars: e,
  varsResolver: t,
  theme: n,
  props: r,
  stylesCtx: o,
  selector: i,
  themeName: l,
  headless: s,
}) {
  var a;
  return (a = Qy([
    s ? {} : t == null ? void 0 : t(n, r, o),
    ...l.map((u) => {
      var f, d, h;
      return (h =
        (d = (f = n.components) == null ? void 0 : f[u]) == null
          ? void 0
          : d.vars) == null
        ? void 0
        : h.call(d, n, r, o);
    }),
    e == null ? void 0 : e(n, r, o),
  ])) == null
    ? void 0
    : a[i];
}
function Yy({
  theme: e,
  themeName: t,
  selector: n,
  options: r,
  props: o,
  stylesCtx: i,
  rootSelector: l,
  styles: s,
  style: a,
  vars: u,
  varsResolver: f,
  headless: d,
  withStylesTransform: h,
}) {
  return {
    ...(!h &&
      by({ theme: e, themeName: t, props: o, stylesCtx: i, selector: n })),
    ...(!h && Zl({ theme: e, styles: s, props: o, stylesCtx: i })[n]),
    ...(!h &&
      Zl({
        theme: e,
        styles: r == null ? void 0 : r.styles,
        props: (r == null ? void 0 : r.props) || o,
        stylesCtx: i,
      })[n]),
    ...Gy({
      theme: e,
      props: o,
      stylesCtx: i,
      vars: u,
      varsResolver: f,
      selector: n,
      themeName: t,
      headless: d,
    }),
    ...(l === n ? ql({ style: a, theme: e }) : null),
    ...ql({ style: r == null ? void 0 : r.style, theme: e }),
  };
}
function Ky({ props: e, stylesCtx: t, themeName: n }) {
  var l;
  const r = Et(),
    o = (l = my()) == null ? void 0 : l();
  return {
    getTransformedStyles: (s) =>
      o
        ? [
            ...s.map((u) => o(u, { props: e, theme: r, ctx: t })),
            ...n.map((u) => {
              var f;
              return o((f = r.components[u]) == null ? void 0 : f.styles, {
                props: e,
                theme: r,
                ctx: t,
              });
            }),
          ].filter(Boolean)
        : [],
    withStylesTransform: !!o,
  };
}
function ue({
  name: e,
  classes: t,
  props: n,
  stylesCtx: r,
  className: o,
  style: i,
  rootSelector: l = "root",
  unstyled: s,
  classNames: a,
  styles: u,
  vars: f,
  varsResolver: d,
}) {
  const h = Et(),
    g = cy(),
    y = fy(),
    v = dy(),
    C = (Array.isArray(e) ? e : [e]).filter((p) => p),
    { withStylesTransform: m, getTransformedStyles: c } = Ky({
      props: n,
      stylesCtx: r,
      themeName: C,
    });
  return (p, S) => ({
    className: Hy({
      theme: h,
      options: S,
      themeName: C,
      selector: p,
      classNamesPrefix: g,
      classNames: a,
      classes: t,
      unstyled: s,
      className: o,
      rootSelector: l,
      props: n,
      stylesCtx: r,
      withStaticClasses: y,
      headless: v,
      transformedStyles: c([S == null ? void 0 : S.styles, u]),
    }),
    style: Yy({
      theme: h,
      themeName: C,
      selector: p,
      options: S,
      props: n,
      stylesCtx: r,
      rootSelector: l,
      styles: u,
      style: i,
      vars: f,
      varsResolver: d,
      headless: v,
      withStylesTransform: m,
    }),
  });
}
function Od(e, t) {
  return typeof e == "boolean" ? e : t.autoContrast;
}
function H(e, t, n) {
  var l;
  const r = Et(),
    o = (l = r.components[e]) == null ? void 0 : l.defaultProps,
    i = typeof o == "function" ? o(r) : o;
  return { ...t, ...i, ...Ur(n) };
}
function nl(e) {
  return ke(e)
    .reduce((t, n) => (e[n] !== void 0 ? `${t}${bh(n)}:${e[n]};` : t), "")
    .trim();
}
function Xy({ selector: e, styles: t, media: n, container: r }) {
  const o = t ? nl(t) : "",
    i = Array.isArray(n)
      ? n.map((s) => `@media${s.query}{${e}{${nl(s.styles)}}}`)
      : [],
    l = Array.isArray(r)
      ? r.map((s) => `@container ${s.query}{${e}{${nl(s.styles)}}}`)
      : [];
  return `${o ? `${e}{${o}}` : ""}${i.join("")}${l.join("")}`.trim();
}
function ca(e) {
  const t = ia();
  return k.jsx("style", {
    "data-mantine-styles": "inline",
    nonce: t == null ? void 0 : t(),
    dangerouslySetInnerHTML: { __html: Xy(e) },
  });
}
function pi(e) {
  const {
    m: t,
    mx: n,
    my: r,
    mt: o,
    mb: i,
    ml: l,
    mr: s,
    me: a,
    ms: u,
    p: f,
    px: d,
    py: h,
    pt: g,
    pb: y,
    pl: v,
    pr: C,
    pe: m,
    ps: c,
    bd: p,
    bg: S,
    c: _,
    opacity: w,
    ff: E,
    fz: N,
    fw: I,
    lts: O,
    ta: b,
    lh: ie,
    fs: W,
    tt: le,
    td: Xe,
    w: ce,
    miw: je,
    maw: T,
    h: L,
    mih: z,
    mah: j,
    bgsz: F,
    bgp: B,
    bgr: J,
    bga: Oe,
    pos: fe,
    top: ne,
    left: _t,
    bottom: Ci,
    right: ap,
    inset: up,
    display: cp,
    flex: fp,
    hiddenFrom: dp,
    visibleFrom: pp,
    lightHidden: mp,
    darkHidden: hp,
    sx: yp,
    ...vp
  } = e;
  return {
    styleProps: Ur({
      m: t,
      mx: n,
      my: r,
      mt: o,
      mb: i,
      ml: l,
      mr: s,
      me: a,
      ms: u,
      p: f,
      px: d,
      py: h,
      pt: g,
      pb: y,
      pl: v,
      pr: C,
      pe: m,
      ps: c,
      bd: p,
      bg: S,
      c: _,
      opacity: w,
      ff: E,
      fz: N,
      fw: I,
      lts: O,
      ta: b,
      lh: ie,
      fs: W,
      tt: le,
      td: Xe,
      w: ce,
      miw: je,
      maw: T,
      h: L,
      mih: z,
      mah: j,
      bgsz: F,
      bgp: B,
      bgr: J,
      bga: Oe,
      pos: fe,
      top: ne,
      left: _t,
      bottom: Ci,
      right: ap,
      inset: up,
      display: cp,
      flex: fp,
      hiddenFrom: dp,
      visibleFrom: pp,
      lightHidden: mp,
      darkHidden: hp,
      sx: yp,
    }),
    rest: vp,
  };
}
const Zy = {
  m: { type: "spacing", property: "margin" },
  mt: { type: "spacing", property: "marginTop" },
  mb: { type: "spacing", property: "marginBottom" },
  ml: { type: "spacing", property: "marginLeft" },
  mr: { type: "spacing", property: "marginRight" },
  ms: { type: "spacing", property: "marginInlineStart" },
  me: { type: "spacing", property: "marginInlineEnd" },
  mx: { type: "spacing", property: "marginInline" },
  my: { type: "spacing", property: "marginBlock" },
  p: { type: "spacing", property: "padding" },
  pt: { type: "spacing", property: "paddingTop" },
  pb: { type: "spacing", property: "paddingBottom" },
  pl: { type: "spacing", property: "paddingLeft" },
  pr: { type: "spacing", property: "paddingRight" },
  ps: { type: "spacing", property: "paddingInlineStart" },
  pe: { type: "spacing", property: "paddingInlineEnd" },
  px: { type: "spacing", property: "paddingInline" },
  py: { type: "spacing", property: "paddingBlock" },
  bd: { type: "border", property: "border" },
  bg: { type: "color", property: "background" },
  c: { type: "textColor", property: "color" },
  opacity: { type: "identity", property: "opacity" },
  ff: { type: "fontFamily", property: "fontFamily" },
  fz: { type: "fontSize", property: "fontSize" },
  fw: { type: "identity", property: "fontWeight" },
  lts: { type: "size", property: "letterSpacing" },
  ta: { type: "identity", property: "textAlign" },
  lh: { type: "lineHeight", property: "lineHeight" },
  fs: { type: "identity", property: "fontStyle" },
  tt: { type: "identity", property: "textTransform" },
  td: { type: "identity", property: "textDecoration" },
  w: { type: "spacing", property: "width" },
  miw: { type: "spacing", property: "minWidth" },
  maw: { type: "spacing", property: "maxWidth" },
  h: { type: "spacing", property: "height" },
  mih: { type: "spacing", property: "minHeight" },
  mah: { type: "spacing", property: "maxHeight" },
  bgsz: { type: "size", property: "backgroundSize" },
  bgp: { type: "identity", property: "backgroundPosition" },
  bgr: { type: "identity", property: "backgroundRepeat" },
  bga: { type: "identity", property: "backgroundAttachment" },
  pos: { type: "identity", property: "position" },
  top: { type: "identity", property: "top" },
  left: { type: "size", property: "left" },
  bottom: { type: "size", property: "bottom" },
  right: { type: "size", property: "right" },
  inset: { type: "size", property: "inset" },
  display: { type: "identity", property: "display" },
  flex: { type: "identity", property: "flex" },
};
function fa(e, t) {
  const n = un({ color: e, theme: t });
  return n.color === "dimmed"
    ? "var(--mantine-color-dimmed)"
    : n.color === "bright"
    ? "var(--mantine-color-bright)"
    : n.variable
    ? `var(${n.variable})`
    : n.color;
}
function Jy(e, t) {
  const n = un({ color: e, theme: t });
  return n.isThemeColor && n.shade === void 0
    ? `var(--mantine-color-${n.color}-text)`
    : fa(e, t);
}
function qy(e, t) {
  if (typeof e == "number") return $(e);
  if (typeof e == "string") {
    const [n, r, ...o] = e.split(" ").filter((l) => l.trim() !== "");
    let i = `${$(n)}`;
    return (
      r && (i += ` ${r}`),
      o.length > 0 && (i += ` ${fa(o.join(" "), t)}`),
      i.trim()
    );
  }
  return e;
}
const Au = {
  text: "var(--mantine-font-family)",
  mono: "var(--mantine-font-family-monospace)",
  monospace: "var(--mantine-font-family-monospace)",
  heading: "var(--mantine-font-family-headings)",
  headings: "var(--mantine-font-family-headings)",
};
function ev(e) {
  return typeof e == "string" && e in Au ? Au[e] : e;
}
const tv = ["h1", "h2", "h3", "h4", "h5", "h6"];
function nv(e, t) {
  return typeof e == "string" && e in t.fontSizes
    ? `var(--mantine-font-size-${e})`
    : typeof e == "string" && tv.includes(e)
    ? `var(--mantine-${e}-font-size)`
    : typeof e == "number" || typeof e == "string"
    ? $(e)
    : e;
}
function rv(e) {
  return e;
}
const ov = ["h1", "h2", "h3", "h4", "h5", "h6"];
function iv(e, t) {
  return typeof e == "string" && e in t.lineHeights
    ? `var(--mantine-line-height-${e})`
    : typeof e == "string" && ov.includes(e)
    ? `var(--mantine-${e}-line-height)`
    : e;
}
function lv(e) {
  return typeof e == "number" ? $(e) : e;
}
function sv(e, t) {
  if (typeof e == "number") return $(e);
  if (typeof e == "string") {
    const n = e.replace("-", "");
    if (!(n in t.spacing)) return $(e);
    const r = `--mantine-spacing-${n}`;
    return e.startsWith("-") ? `calc(var(${r}) * -1)` : `var(${r})`;
  }
  return e;
}
const rl = {
  color: fa,
  textColor: Jy,
  fontSize: nv,
  spacing: sv,
  identity: rv,
  size: lv,
  lineHeight: iv,
  fontFamily: ev,
  border: qy,
};
function Bu(e) {
  return e.replace("(min-width: ", "").replace("em)", "");
}
function av({ media: e, ...t }) {
  const r = Object.keys(e)
    .sort((o, i) => Number(Bu(o)) - Number(Bu(i)))
    .map((o) => ({ query: o, styles: e[o] }));
  return { ...t, media: r };
}
function uv(e) {
  if (typeof e != "object" || e === null) return !1;
  const t = Object.keys(e);
  return !(t.length === 1 && t[0] === "base");
}
function cv(e) {
  return typeof e == "object" && e !== null
    ? "base" in e
      ? e.base
      : void 0
    : e;
}
function fv(e) {
  return typeof e == "object" && e !== null
    ? ke(e).filter((t) => t !== "base")
    : [];
}
function dv(e, t) {
  return typeof e == "object" && e !== null && t in e ? e[t] : e;
}
function pv({ styleProps: e, data: t, theme: n }) {
  return av(
    ke(e).reduce(
      (r, o) => {
        if (o === "hiddenFrom" || o === "visibleFrom" || o === "sx") return r;
        const i = t[o],
          l = Array.isArray(i.property) ? i.property : [i.property],
          s = cv(e[o]);
        if (!uv(e[o]))
          return (
            l.forEach((u) => {
              r.inlineStyles[u] = rl[i.type](s, n);
            }),
            r
          );
        r.hasResponsiveStyles = !0;
        const a = fv(e[o]);
        return (
          l.forEach((u) => {
            s && (r.styles[u] = rl[i.type](s, n)),
              a.forEach((f) => {
                const d = `(min-width: ${n.breakpoints[f]})`;
                r.media[d] = { ...r.media[d], [u]: rl[i.type](dv(e[o], f), n) };
              });
          }),
          r
        );
      },
      { hasResponsiveStyles: !1, styles: {}, inlineStyles: {}, media: {} }
    )
  );
}
function da() {
  return `__m__-${x.useId().replace(/:/g, "")}`;
}
function Fd(e) {
  return e.startsWith("data-") ? e : `data-${e}`;
}
function mv(e) {
  return Object.keys(e).reduce((t, n) => {
    const r = e[n];
    return (
      r === void 0 || r === "" || r === !1 || r === null || (t[Fd(n)] = e[n]), t
    );
  }, {});
}
function Md(e) {
  return e
    ? typeof e == "string"
      ? { [Fd(e)]: !0 }
      : Array.isArray(e)
      ? [...e].reduce((t, n) => ({ ...t, ...Md(n) }), {})
      : mv(e)
    : null;
}
function es(e, t) {
  return Array.isArray(e)
    ? [...e].reduce((n, r) => ({ ...n, ...es(r, t) }), {})
    : typeof e == "function"
    ? e(t)
    : e ?? {};
}
function hv({ theme: e, style: t, vars: n, styleProps: r }) {
  const o = es(t, e),
    i = es(n, e);
  return { ...o, ...i, ...r };
}
const Dd = x.forwardRef(
  (
    {
      component: e,
      style: t,
      __vars: n,
      className: r,
      variant: o,
      mod: i,
      size: l,
      hiddenFrom: s,
      visibleFrom: a,
      lightHidden: u,
      darkHidden: f,
      renderRoot: d,
      __size: h,
      ...g
    },
    y
  ) => {
    var N;
    const v = Et(),
      C = e || "div",
      { styleProps: m, rest: c } = pi(g),
      p = py(),
      S = (N = p == null ? void 0 : p()) == null ? void 0 : N(m.sx),
      _ = da(),
      w = pv({ styleProps: m, theme: v, data: Zy }),
      E = {
        ref: y,
        style: hv({ theme: v, style: t, vars: n, styleProps: w.inlineStyles }),
        className: Ct(r, S, {
          [_]: w.hasResponsiveStyles,
          "mantine-light-hidden": u,
          "mantine-dark-hidden": f,
          [`mantine-hidden-from-${s}`]: s,
          [`mantine-visible-from-${a}`]: a,
        }),
        "data-variant": o,
        "data-size": _d(l) ? void 0 : l || void 0,
        size: h,
        ...Md(i),
        ...c,
      };
    return k.jsxs(k.Fragment, {
      children: [
        w.hasResponsiveStyles &&
          k.jsx(ca, { selector: `.${_}`, styles: w.styles, media: w.media }),
        typeof d == "function" ? d(E) : k.jsx(C, { ...E }),
      ],
    });
  }
);
Dd.displayName = "@mantine/core/Box";
const V = Dd;
function Vd(e) {
  return e;
}
function Ce(e) {
  const t = x.forwardRef(e);
  return (
    (t.extend = Vd),
    (t.withProps = (n) => {
      const r = x.forwardRef((o, i) => k.jsx(t, { ...n, ...o, ref: i }));
      return (
        (r.extend = t.extend),
        (r.displayName = `WithProps(${t.displayName})`),
        r
      );
    }),
    t
  );
}
function Hn(e) {
  const t = x.forwardRef(e);
  return (
    (t.withProps = (n) => {
      const r = x.forwardRef((o, i) => k.jsx(t, { ...n, ...o, ref: i }));
      return (
        (r.extend = t.extend),
        (r.displayName = `WithProps(${t.displayName})`),
        r
      );
    }),
    (t.extend = Vd),
    t
  );
}
var Ad = { root: "m_87cf2631" };
const yv = { __staticSelector: "UnstyledButton" },
  mi = Hn((e, t) => {
    const n = H("UnstyledButton", yv, e),
      {
        className: r,
        component: o = "button",
        __staticSelector: i,
        unstyled: l,
        classNames: s,
        styles: a,
        style: u,
        ...f
      } = n,
      d = ue({
        name: i,
        props: n,
        classes: Ad,
        className: r,
        style: u,
        classNames: s,
        styles: a,
        unstyled: l,
      });
    return k.jsx(V, {
      ...d("root", { focusable: !0 }),
      component: o,
      ref: t,
      type: o === "button" ? "button" : void 0,
      ...f,
    });
  });
mi.classes = Ad;
mi.displayName = "@mantine/core/UnstyledButton";
const nr = (e) => ({
    in: { opacity: 1, transform: "scale(1)" },
    out: {
      opacity: 0,
      transform: `scale(.9) translateY(${$(e === "bottom" ? 10 : -10)})`,
    },
    transitionProperty: "transform, opacity",
  }),
  fo = {
    fade: {
      in: { opacity: 1 },
      out: { opacity: 0 },
      transitionProperty: "opacity",
    },
    "fade-up": {
      in: { opacity: 1, transform: "translateY(0)" },
      out: { opacity: 0, transform: `translateY(${$(30)}` },
      transitionProperty: "opacity, transform",
    },
    "fade-down": {
      in: { opacity: 1, transform: "translateY(0)" },
      out: { opacity: 0, transform: `translateY(${$(-30)}` },
      transitionProperty: "opacity, transform",
    },
    "fade-left": {
      in: { opacity: 1, transform: "translateX(0)" },
      out: { opacity: 0, transform: `translateX(${$(30)}` },
      transitionProperty: "opacity, transform",
    },
    "fade-right": {
      in: { opacity: 1, transform: "translateX(0)" },
      out: { opacity: 0, transform: `translateX(${$(-30)}` },
      transitionProperty: "opacity, transform",
    },
    scale: {
      in: { opacity: 1, transform: "scale(1)" },
      out: { opacity: 0, transform: "scale(0)" },
      common: { transformOrigin: "top" },
      transitionProperty: "transform, opacity",
    },
    "scale-y": {
      in: { opacity: 1, transform: "scaleY(1)" },
      out: { opacity: 0, transform: "scaleY(0)" },
      common: { transformOrigin: "top" },
      transitionProperty: "transform, opacity",
    },
    "scale-x": {
      in: { opacity: 1, transform: "scaleX(1)" },
      out: { opacity: 0, transform: "scaleX(0)" },
      common: { transformOrigin: "left" },
      transitionProperty: "transform, opacity",
    },
    "skew-up": {
      in: { opacity: 1, transform: "translateY(0) skew(0deg, 0deg)" },
      out: {
        opacity: 0,
        transform: `translateY(${$(-20)}) skew(-10deg, -5deg)`,
      },
      common: { transformOrigin: "top" },
      transitionProperty: "transform, opacity",
    },
    "skew-down": {
      in: { opacity: 1, transform: "translateY(0) skew(0deg, 0deg)" },
      out: {
        opacity: 0,
        transform: `translateY(${$(20)}) skew(-10deg, -5deg)`,
      },
      common: { transformOrigin: "bottom" },
      transitionProperty: "transform, opacity",
    },
    "rotate-left": {
      in: { opacity: 1, transform: "translateY(0) rotate(0deg)" },
      out: { opacity: 0, transform: `translateY(${$(20)}) rotate(-5deg)` },
      common: { transformOrigin: "bottom" },
      transitionProperty: "transform, opacity",
    },
    "rotate-right": {
      in: { opacity: 1, transform: "translateY(0) rotate(0deg)" },
      out: { opacity: 0, transform: `translateY(${$(20)}) rotate(5deg)` },
      common: { transformOrigin: "top" },
      transitionProperty: "transform, opacity",
    },
    "slide-down": {
      in: { opacity: 1, transform: "translateY(0)" },
      out: { opacity: 0, transform: "translateY(-100%)" },
      common: { transformOrigin: "top" },
      transitionProperty: "transform, opacity",
    },
    "slide-up": {
      in: { opacity: 1, transform: "translateY(0)" },
      out: { opacity: 0, transform: "translateY(100%)" },
      common: { transformOrigin: "bottom" },
      transitionProperty: "transform, opacity",
    },
    "slide-left": {
      in: { opacity: 1, transform: "translateX(0)" },
      out: { opacity: 0, transform: "translateX(100%)" },
      common: { transformOrigin: "left" },
      transitionProperty: "transform, opacity",
    },
    "slide-right": {
      in: { opacity: 1, transform: "translateX(0)" },
      out: { opacity: 0, transform: "translateX(-100%)" },
      common: { transformOrigin: "right" },
      transitionProperty: "transform, opacity",
    },
    pop: { ...nr("bottom"), common: { transformOrigin: "center center" } },
    "pop-bottom-left": {
      ...nr("bottom"),
      common: { transformOrigin: "bottom left" },
    },
    "pop-bottom-right": {
      ...nr("bottom"),
      common: { transformOrigin: "bottom right" },
    },
    "pop-top-left": { ...nr("top"), common: { transformOrigin: "top left" } },
    "pop-top-right": { ...nr("top"), common: { transformOrigin: "top right" } },
  },
  Wu = {
    entering: "in",
    entered: "in",
    exiting: "out",
    exited: "out",
    "pre-exiting": "out",
    "pre-entering": "out",
  };
function vv({ transition: e, state: t, duration: n, timingFunction: r }) {
  const o = { transitionDuration: `${n}ms`, transitionTimingFunction: r };
  return typeof e == "string"
    ? e in fo
      ? {
          transitionProperty: fo[e].transitionProperty,
          ...o,
          ...fo[e].common,
          ...fo[e][Wu[t]],
        }
      : {}
    : {
        transitionProperty: e.transitionProperty,
        ...o,
        ...e.common,
        ...e[Wu[t]],
      };
}
function gv({
  duration: e,
  exitDuration: t,
  timingFunction: n,
  mounted: r,
  onEnter: o,
  onExit: i,
  onEntered: l,
  onExited: s,
  enterDelay: a,
  exitDelay: u,
}) {
  const f = Et(),
    d = oy(),
    h = f.respectReducedMotion ? d : !1,
    [g, y] = x.useState(h ? 0 : e),
    [v, C] = x.useState(r ? "entered" : "exited"),
    m = x.useRef(-1),
    c = x.useRef(-1),
    p = x.useRef(-1),
    S = (w) => {
      const E = w ? o : i,
        N = w ? l : s;
      window.clearTimeout(m.current);
      const I = h ? 0 : w ? e : t;
      y(I),
        I === 0
          ? (typeof E == "function" && E(),
            typeof N == "function" && N(),
            C(w ? "entered" : "exited"))
          : (p.current = requestAnimationFrame(() => {
              Hh.flushSync(() => {
                C(w ? "pre-entering" : "pre-exiting");
              }),
                (p.current = requestAnimationFrame(() => {
                  typeof E == "function" && E(),
                    C(w ? "entering" : "exiting"),
                    (m.current = window.setTimeout(() => {
                      typeof N == "function" && N(),
                        C(w ? "entered" : "exited");
                    }, I));
                }));
            }));
    },
    _ = (w) => {
      if ((window.clearTimeout(c.current), typeof (w ? a : u) != "number")) {
        S(w);
        return;
      }
      c.current = window.setTimeout(
        () => {
          S(w);
        },
        w ? a : u
      );
    };
  return (
    ey(() => {
      _(r);
    }, [r]),
    x.useEffect(
      () => () => {
        window.clearTimeout(m.current), cancelAnimationFrame(p.current);
      },
      []
    ),
    {
      transitionDuration: g,
      transitionStatus: v,
      transitionTimingFunction: n || "ease",
    }
  );
}
function Bd({
  keepMounted: e,
  transition: t = "fade",
  duration: n = 250,
  exitDuration: r = n,
  mounted: o,
  children: i,
  timingFunction: l = "ease",
  onExit: s,
  onEntered: a,
  onEnter: u,
  onExited: f,
  enterDelay: d,
  exitDelay: h,
}) {
  const {
    transitionDuration: g,
    transitionStatus: y,
    transitionTimingFunction: v,
  } = gv({
    mounted: o,
    exitDuration: r,
    duration: n,
    timingFunction: l,
    onExit: s,
    onEntered: a,
    onEnter: u,
    onExited: f,
    enterDelay: d,
    exitDelay: h,
  });
  return g === 0
    ? o
      ? k.jsx(k.Fragment, { children: i({}) })
      : e
      ? i({ display: "none" })
      : null
    : y === "exited"
    ? e
      ? i({ display: "none" })
      : null
    : k.jsx(k.Fragment, {
        children: i(
          vv({ transition: t, duration: g, state: y, timingFunction: v })
        ),
      });
}
Bd.displayName = "@mantine/core/Transition";
var nt = {
  root: "m_5ae2e3c",
  barsLoader: "m_7a2bd4cd",
  bar: "m_870bb79",
  "bars-loader-animation": "m_5d2b3b9d",
  dotsLoader: "m_4e3f22d7",
  dot: "m_870c4af",
  "loader-dots-animation": "m_aac34a1",
  ovalLoader: "m_b34414df",
  "oval-loader-animation": "m_f8e89c4b",
};
const Wd = x.forwardRef(({ className: e, ...t }, n) =>
  k.jsxs(V, {
    component: "span",
    className: Ct(nt.barsLoader, e),
    ...t,
    ref: n,
    children: [
      k.jsx("span", { className: nt.bar }),
      k.jsx("span", { className: nt.bar }),
      k.jsx("span", { className: nt.bar }),
    ],
  })
);
Wd.displayName = "@mantine/core/Bars";
const Ud = x.forwardRef(({ className: e, ...t }, n) =>
  k.jsxs(V, {
    component: "span",
    className: Ct(nt.dotsLoader, e),
    ...t,
    ref: n,
    children: [
      k.jsx("span", { className: nt.dot }),
      k.jsx("span", { className: nt.dot }),
      k.jsx("span", { className: nt.dot }),
    ],
  })
);
Ud.displayName = "@mantine/core/Dots";
const Hd = x.forwardRef(({ className: e, ...t }, n) =>
  k.jsx(V, { component: "span", className: Ct(nt.ovalLoader, e), ...t, ref: n })
);
Hd.displayName = "@mantine/core/Oval";
const bd = { bars: Wd, oval: Hd, dots: Ud },
  wv = { loaders: bd, type: "oval" },
  Sv = (e, { size: t, color: n }) => ({
    root: {
      "--loader-size": Ye(t, "loader-size"),
      "--loader-color": n ? Ut(n, e) : void 0,
    },
  }),
  hi = Ce((e, t) => {
    const n = H("Loader", wv, e),
      {
        size: r,
        color: o,
        type: i,
        vars: l,
        className: s,
        style: a,
        classNames: u,
        styles: f,
        unstyled: d,
        loaders: h,
        variant: g,
        children: y,
        ...v
      } = n,
      C = ue({
        name: "Loader",
        props: n,
        classes: nt,
        className: s,
        style: a,
        classNames: u,
        styles: f,
        unstyled: d,
        vars: l,
        varsResolver: Sv,
      });
    return y
      ? k.jsx(V, { ...C("root"), ref: t, ...v, children: y })
      : k.jsx(V, {
          ...C("root"),
          ref: t,
          component: h[i],
          variant: g,
          size: r,
          ...v,
        });
  });
hi.defaultLoaders = bd;
hi.classes = nt;
hi.displayName = "@mantine/core/Loader";
function kv(e) {
  return x.Children.toArray(e).filter(Boolean);
}
var Qd = { root: "m_4081bf90" };
const xv = {
    preventGrowOverflow: !0,
    gap: "md",
    align: "center",
    justify: "flex-start",
    wrap: "wrap",
  },
  Cv = (
    e,
    { grow: t, preventGrowOverflow: n, gap: r, align: o, justify: i, wrap: l },
    { childWidth: s }
  ) => ({
    root: {
      "--group-child-width": t && n ? s : void 0,
      "--group-gap": Or(r),
      "--group-align": o,
      "--group-justify": i,
      "--group-wrap": l,
    },
  }),
  pa = Ce((e, t) => {
    const n = H("Group", xv, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        children: a,
        gap: u,
        align: f,
        justify: d,
        wrap: h,
        grow: g,
        preventGrowOverflow: y,
        vars: v,
        variant: C,
        __size: m,
        mod: c,
        ...p
      } = n,
      S = kv(a),
      _ = S.length,
      w = Or(u ?? "md"),
      N = { childWidth: `calc(${100 / _}% - (${w} - ${w} / ${_}))` },
      I = ue({
        name: "Group",
        props: n,
        stylesCtx: N,
        className: o,
        style: i,
        classes: Qd,
        classNames: r,
        styles: l,
        unstyled: s,
        vars: v,
        varsResolver: Cv,
      });
    return k.jsx(V, {
      ...I("root"),
      ref: t,
      variant: C,
      mod: [{ grow: g }, c],
      size: m,
      ...p,
      children: S,
    });
  });
pa.classes = Qd;
pa.displayName = "@mantine/core/Group";
const [Ev, br] = $d({
  offsetBottom: !1,
  offsetTop: !1,
  describedBy: void 0,
  getStyles: null,
  inputId: void 0,
  labelId: void 0,
});
var Ke = {
  wrapper: "m_6c018570",
  input: "m_8fb7ebe7",
  section: "m_82577fc2",
  placeholder: "m_88bacfd0",
  root: "m_46b77525",
  label: "m_8fdc1311",
  required: "m_78a94662",
  error: "m_8f816625",
  description: "m_fe47ce59",
};
const Uu = {},
  _v = (e, { size: t }) => ({
    description: {
      "--input-description-size":
        t === void 0 ? void 0 : `calc(${it(t)} - ${$(2)})`,
    },
  }),
  yi = Ce((e, t) => {
    const n = H("InputDescription", Uu, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        size: u,
        __staticSelector: f,
        __inheritStyles: d = !0,
        variant: h,
        ...g
      } = H("InputDescription", Uu, n),
      y = br(),
      v = ue({
        name: ["InputWrapper", f],
        props: n,
        classes: Ke,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        rootSelector: "description",
        vars: a,
        varsResolver: _v,
      }),
      C = (d && (y == null ? void 0 : y.getStyles)) || v;
    return k.jsx(V, {
      component: "p",
      ref: t,
      variant: h,
      size: u,
      ...C(
        "description",
        y != null && y.getStyles ? { className: o, style: i } : void 0
      ),
      ...g,
    });
  });
yi.classes = Ke;
yi.displayName = "@mantine/core/InputDescription";
const $v = {},
  Nv = (e, { size: t }) => ({
    error: {
      "--input-error-size": t === void 0 ? void 0 : `calc(${it(t)} - ${$(2)})`,
    },
  }),
  vi = Ce((e, t) => {
    const n = H("InputError", $v, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        size: u,
        __staticSelector: f,
        __inheritStyles: d = !0,
        variant: h,
        ...g
      } = n,
      y = ue({
        name: ["InputWrapper", f],
        props: n,
        classes: Ke,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        rootSelector: "error",
        vars: a,
        varsResolver: Nv,
      }),
      v = br(),
      C = (d && (v == null ? void 0 : v.getStyles)) || y;
    return k.jsx(V, {
      component: "p",
      ref: t,
      variant: h,
      size: u,
      ...C(
        "error",
        v != null && v.getStyles ? { className: o, style: i } : void 0
      ),
      ...g,
    });
  });
vi.classes = Ke;
vi.displayName = "@mantine/core/InputError";
const Hu = { labelElement: "label" },
  Pv = (e, { size: t }) => ({
    label: { "--input-label-size": it(t), "--input-asterisk-color": void 0 },
  }),
  gi = Ce((e, t) => {
    const n = H("InputLabel", Hu, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        labelElement: u,
        size: f,
        required: d,
        htmlFor: h,
        onMouseDown: g,
        children: y,
        __staticSelector: v,
        variant: C,
        mod: m,
        ...c
      } = H("InputLabel", Hu, n),
      p = ue({
        name: ["InputWrapper", v],
        props: n,
        classes: Ke,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        rootSelector: "label",
        vars: a,
        varsResolver: Pv,
      }),
      S = br(),
      _ = (S == null ? void 0 : S.getStyles) || p;
    return k.jsxs(V, {
      ..._(
        "label",
        S != null && S.getStyles ? { className: o, style: i } : void 0
      ),
      component: u,
      variant: C,
      size: f,
      ref: t,
      htmlFor: u === "label" ? h : void 0,
      mod: [{ required: d }, m],
      onMouseDown: (w) => {
        g == null || g(w),
          !w.defaultPrevented && w.detail > 1 && w.preventDefault();
      },
      ...c,
      children: [
        y,
        d &&
          k.jsx("span", {
            ..._("required"),
            "aria-hidden": !0,
            children: " *",
          }),
      ],
    });
  });
gi.classes = Ke;
gi.displayName = "@mantine/core/InputLabel";
const bu = {},
  ma = Ce((e, t) => {
    const n = H("InputPlaceholder", bu, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        __staticSelector: u,
        variant: f,
        error: d,
        mod: h,
        ...g
      } = H("InputPlaceholder", bu, n),
      y = ue({
        name: ["InputPlaceholder", u],
        props: n,
        classes: Ke,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        rootSelector: "placeholder",
      });
    return k.jsx(V, {
      ...y("placeholder"),
      mod: [{ error: !!d }, h],
      component: "span",
      variant: f,
      ref: t,
      ...g,
    });
  });
ma.classes = Ke;
ma.displayName = "@mantine/core/InputPlaceholder";
function jv(e, { hasDescription: t, hasError: n }) {
  const r = e.findIndex((a) => a === "input"),
    o = e.slice(0, r),
    i = e.slice(r + 1),
    l = (t && o.includes("description")) || (n && o.includes("error"));
  return {
    offsetBottom:
      (t && i.includes("description")) || (n && i.includes("error")),
    offsetTop: l,
  };
}
const Tv = {
    labelElement: "label",
    inputContainer: (e) => e,
    inputWrapperOrder: ["label", "description", "input", "error"],
  },
  Rv = (e, { size: t }) => ({
    label: { "--input-label-size": it(t), "--input-asterisk-color": void 0 },
    error: {
      "--input-error-size": t === void 0 ? void 0 : `calc(${it(t)} - ${$(2)})`,
    },
    description: {
      "--input-description-size":
        t === void 0 ? void 0 : `calc(${it(t)} - ${$(2)})`,
    },
  }),
  ha = Ce((e, t) => {
    const n = H("InputWrapper", Tv, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        size: u,
        variant: f,
        __staticSelector: d,
        inputContainer: h,
        inputWrapperOrder: g,
        label: y,
        error: v,
        description: C,
        labelProps: m,
        descriptionProps: c,
        errorProps: p,
        labelElement: S,
        children: _,
        withAsterisk: w,
        id: E,
        required: N,
        __stylesApiProps: I,
        mod: O,
        ...b
      } = n,
      ie = ue({
        name: ["InputWrapper", d],
        props: I || n,
        classes: Ke,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        vars: a,
        varsResolver: Rv,
      }),
      W = { size: u, variant: f, __staticSelector: d },
      le = Pd(E),
      Xe = typeof w == "boolean" ? w : N,
      ce = (p == null ? void 0 : p.id) || `${le}-error`,
      je = (c == null ? void 0 : c.id) || `${le}-description`,
      T = le,
      L = !!v && typeof v != "boolean",
      z = !!C,
      j = `${L ? ce : ""} ${z ? je : ""}`,
      F = j.trim().length > 0 ? j.trim() : void 0,
      B = (m == null ? void 0 : m.id) || `${le}-label`,
      J =
        y &&
        k.jsx(
          gi,
          {
            labelElement: S,
            id: B,
            htmlFor: T,
            required: Xe,
            ...W,
            ...m,
            children: y,
          },
          "label"
        ),
      Oe =
        z &&
        k.jsx(
          yi,
          {
            ...c,
            ...W,
            size: (c == null ? void 0 : c.size) || W.size,
            id: (c == null ? void 0 : c.id) || je,
            children: C,
          },
          "description"
        ),
      fe = k.jsx(x.Fragment, { children: h(_) }, "input"),
      ne =
        L &&
        x.createElement(
          vi,
          {
            ...p,
            ...W,
            size: (p == null ? void 0 : p.size) || W.size,
            key: "error",
            id: (p == null ? void 0 : p.id) || ce,
          },
          v
        ),
      _t = g.map((Ci) => {
        switch (Ci) {
          case "label":
            return J;
          case "input":
            return fe;
          case "description":
            return Oe;
          case "error":
            return ne;
          default:
            return null;
        }
      });
    return k.jsx(Ev, {
      value: {
        getStyles: ie,
        describedBy: F,
        inputId: T,
        labelId: B,
        ...jv(g, { hasDescription: z, hasError: L }),
      },
      children: k.jsx(V, {
        ref: t,
        variant: f,
        size: u,
        mod: [{ error: !!v }, O],
        ...ie("root"),
        ...b,
        children: _t,
      }),
    });
  });
ha.classes = Ke;
ha.displayName = "@mantine/core/InputWrapper";
const zv = {
    variant: "default",
    leftSectionPointerEvents: "none",
    rightSectionPointerEvents: "none",
    withAria: !0,
    withErrorStyles: !0,
  },
  Lv = (e, t, n) => ({
    wrapper: {
      "--input-margin-top": n.offsetTop
        ? "calc(var(--mantine-spacing-xs) / 2)"
        : void 0,
      "--input-margin-bottom": n.offsetBottom
        ? "calc(var(--mantine-spacing-xs) / 2)"
        : void 0,
      "--input-height": Ye(t.size, "input-height"),
      "--input-fz": it(t.size),
      "--input-radius": t.radius === void 0 ? void 0 : Hr(t.radius),
      "--input-left-section-width":
        t.leftSectionWidth !== void 0 ? $(t.leftSectionWidth) : void 0,
      "--input-right-section-width":
        t.rightSectionWidth !== void 0 ? $(t.rightSectionWidth) : void 0,
      "--input-padding-y": t.multiline ? Ye(t.size, "input-padding-y") : void 0,
      "--input-left-section-pointer-events": t.leftSectionPointerEvents,
      "--input-right-section-pointer-events": t.rightSectionPointerEvents,
    },
  }),
  ye = Hn((e, t) => {
    const n = H("Input", zv, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        required: a,
        __staticSelector: u,
        __stylesApiProps: f,
        size: d,
        wrapperProps: h,
        error: g,
        disabled: y,
        leftSection: v,
        leftSectionProps: C,
        leftSectionWidth: m,
        rightSection: c,
        rightSectionProps: p,
        rightSectionWidth: S,
        rightSectionPointerEvents: _,
        leftSectionPointerEvents: w,
        variant: E,
        vars: N,
        pointer: I,
        multiline: O,
        radius: b,
        id: ie,
        withAria: W,
        withErrorStyles: le,
        mod: Xe,
        inputSize: ce,
        ...je
      } = n,
      { styleProps: T, rest: L } = pi(je),
      z = br(),
      j = {
        offsetBottom: z == null ? void 0 : z.offsetBottom,
        offsetTop: z == null ? void 0 : z.offsetTop,
      },
      F = ue({
        name: ["Input", u],
        props: f || n,
        classes: Ke,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        stylesCtx: j,
        rootSelector: "wrapper",
        vars: N,
        varsResolver: Lv,
      }),
      B = W
        ? {
            required: a,
            disabled: y,
            "aria-invalid": !!g,
            "aria-describedby": z == null ? void 0 : z.describedBy,
            id: (z == null ? void 0 : z.inputId) || ie,
          }
        : {};
    return k.jsxs(V, {
      ...F("wrapper"),
      ...T,
      ...h,
      mod: [
        {
          error: !!g && le,
          pointer: I,
          disabled: y,
          multiline: O,
          "data-with-right-section": !!c,
          "data-with-left-section": !!v,
        },
        Xe,
      ],
      variant: E,
      size: d,
      children: [
        v &&
          k.jsx("div", {
            ...C,
            "data-position": "left",
            ...F("section", {
              className: C == null ? void 0 : C.className,
              style: C == null ? void 0 : C.style,
            }),
            children: v,
          }),
        k.jsx(V, {
          component: "input",
          ...L,
          ...B,
          ref: t,
          required: a,
          mod: { disabled: y, error: !!g && le },
          variant: E,
          __size: ce,
          ...F("input"),
        }),
        c &&
          k.jsx("div", {
            ...p,
            "data-position": "right",
            ...F("section", {
              className: p == null ? void 0 : p.className,
              style: p == null ? void 0 : p.style,
            }),
            children: c,
          }),
      ],
    });
  });
ye.classes = Ke;
ye.Wrapper = ha;
ye.Label = gi;
ye.Error = vi;
ye.Description = yi;
ye.Placeholder = ma;
ye.displayName = "@mantine/core/Input";
function Iv(e, t, n) {
  const r = H(e, t, n),
    {
      label: o,
      description: i,
      error: l,
      required: s,
      classNames: a,
      styles: u,
      className: f,
      unstyled: d,
      __staticSelector: h,
      __stylesApiProps: g,
      errorProps: y,
      labelProps: v,
      descriptionProps: C,
      wrapperProps: m,
      id: c,
      size: p,
      style: S,
      inputContainer: _,
      inputWrapperOrder: w,
      withAsterisk: E,
      variant: N,
      vars: I,
      mod: O,
      ...b
    } = r,
    { styleProps: ie, rest: W } = pi(b),
    le = {
      label: o,
      description: i,
      error: l,
      required: s,
      classNames: a,
      className: f,
      __staticSelector: h,
      __stylesApiProps: g || r,
      errorProps: y,
      labelProps: v,
      descriptionProps: C,
      unstyled: d,
      styles: u,
      size: p,
      style: S,
      inputContainer: _,
      inputWrapperOrder: w,
      withAsterisk: E,
      variant: N,
      id: c,
      mod: O,
      ...m,
    };
  return {
    ...W,
    classNames: a,
    styles: u,
    unstyled: d,
    wrapperProps: { ...le, ...ie },
    inputProps: {
      required: s,
      classNames: a,
      styles: u,
      unstyled: d,
      size: p,
      __staticSelector: h,
      __stylesApiProps: g || r,
      error: l,
      variant: N,
      id: c,
    },
  };
}
const Ov = { __staticSelector: "InputBase", withAria: !0 },
  wi = Hn((e, t) => {
    const { inputProps: n, wrapperProps: r, ...o } = Iv("InputBase", Ov, e);
    return k.jsx(ye.Wrapper, {
      ...r,
      children: k.jsx(ye, { ...n, ...o, ref: t }),
    });
  });
wi.classes = { ...ye.classes, ...ye.Wrapper.classes };
wi.displayName = "@mantine/core/InputBase";
var Gd = { root: "m_b6d8b162" };
function Fv(e) {
  if (e === "start") return "start";
  if (e === "end" || e) return "end";
}
const Mv = { inherit: !1 },
  Dv = (e, { variant: t, lineClamp: n, gradient: r, size: o, color: i }) => ({
    root: {
      "--text-fz": it(o),
      "--text-lh": Yh(o),
      "--text-gradient": t === "gradient" ? Jl(r, e) : void 0,
      "--text-line-clamp": typeof n == "number" ? n.toString() : void 0,
      "--text-color": i ? Ut(i, e) : void 0,
    },
  }),
  tt = Hn((e, t) => {
    const n = H("Text", Mv, e),
      {
        lineClamp: r,
        truncate: o,
        inline: i,
        inherit: l,
        gradient: s,
        span: a,
        __staticSelector: u,
        vars: f,
        className: d,
        style: h,
        classNames: g,
        styles: y,
        unstyled: v,
        variant: C,
        mod: m,
        size: c,
        ...p
      } = n,
      S = ue({
        name: ["Text", u],
        props: n,
        classes: Gd,
        className: d,
        style: h,
        classNames: g,
        styles: y,
        unstyled: v,
        vars: f,
        varsResolver: Dv,
      });
    return k.jsx(V, {
      ...S("root", { focusable: !0 }),
      ref: t,
      component: a ? "span" : "p",
      variant: C,
      mod: [
        {
          "data-truncate": Fv(o),
          "data-line-clamp": typeof r == "number",
          "data-inline": i,
          "data-inherit": l,
        },
        m,
      ],
      size: c,
      ...p,
    });
  });
tt.classes = Gd;
tt.displayName = "@mantine/core/Text";
var Yd = { root: "m_849cf0da" };
const Vv = { underline: "hover" },
  ya = Hn((e, t) => {
    const {
      underline: n,
      className: r,
      unstyled: o,
      mod: i,
      ...l
    } = H("Anchor", Vv, e);
    return k.jsx(tt, {
      component: "a",
      ref: t,
      className: Ct({ [Yd.root]: !o }, r),
      ...l,
      mod: [{ underline: n }, i],
      __staticSelector: "Anchor",
      unstyled: o,
    });
  });
ya.classes = Yd;
ya.displayName = "@mantine/core/Anchor";
var Kd = {
  root: "m_5f75b09e",
  body: "m_5f6e695e",
  labelWrapper: "m_d3ea56bb",
  label: "m_8ee546b8",
  description: "m_328f68c0",
  error: "m_8e8a99cc",
};
const Av = Kd,
  Xd = x.forwardRef(
    (
      {
        __staticSelector: e,
        __stylesApiProps: t,
        className: n,
        classNames: r,
        styles: o,
        unstyled: i,
        children: l,
        label: s,
        description: a,
        id: u,
        disabled: f,
        error: d,
        size: h,
        labelPosition: g = "left",
        bodyElement: y = "div",
        labelElement: v = "label",
        variant: C,
        style: m,
        vars: c,
        mod: p,
        ...S
      },
      _
    ) => {
      const w = ue({
        name: e,
        props: t,
        className: n,
        style: m,
        classes: Kd,
        classNames: r,
        styles: o,
        unstyled: i,
      });
      return k.jsx(V, {
        ...w("root"),
        ref: _,
        __vars: { "--label-fz": it(h), "--label-lh": Ye(h, "label-lh") },
        mod: [{ "label-position": g }, p],
        variant: C,
        size: h,
        ...S,
        children: k.jsxs(V, {
          component: y,
          htmlFor: y === "label" ? u : void 0,
          ...w("body"),
          children: [
            l,
            k.jsxs("div", {
              ...w("labelWrapper"),
              "data-disabled": f || void 0,
              children: [
                s &&
                  k.jsx(V, {
                    component: v,
                    htmlFor: v === "label" ? u : void 0,
                    ...w("label"),
                    "data-disabled": f || void 0,
                    children: s,
                  }),
                a &&
                  k.jsx(ye.Description, {
                    size: h,
                    __inheritStyles: !1,
                    ...w("description"),
                    children: a,
                  }),
                d &&
                  typeof d != "boolean" &&
                  k.jsx(ye.Error, {
                    size: h,
                    __inheritStyles: !1,
                    ...w("error"),
                    children: d,
                  }),
              ],
            }),
          ],
        }),
      });
    }
  );
Xd.displayName = "@mantine/core/InlineInput";
const Zd = x.createContext(null),
  Bv = Zd.Provider,
  Jd = () => x.useContext(Zd),
  [Wv, Uv] = $d();
var qd = { card: "m_26775b0a" };
const Hv = { withBorder: !0 },
  bv = (e, { radius: t }) => ({ card: { "--card-radius": Hr(t) } }),
  va = Ce((e, t) => {
    const n = H("CheckboxCard", Hv, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        checked: u,
        mod: f,
        withBorder: d,
        value: h,
        onClick: g,
        ...y
      } = n,
      v = ue({
        name: "CheckboxCard",
        classes: qd,
        props: n,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        vars: a,
        varsResolver: bv,
        rootSelector: "card",
      }),
      C = Jd(),
      m =
        typeof u == "boolean"
          ? u
          : (C == null ? void 0 : C.value.includes(h || "")) || !1;
    return k.jsx(Wv, {
      value: { checked: m },
      children: k.jsx(mi, {
        ref: t,
        mod: [{ "with-border": d, checked: m }, f],
        ...v("card"),
        ...y,
        role: "checkbox",
        "aria-checked": m,
        onClick: (c) => {
          g == null || g(c), C == null || C.onChange(h || "");
        },
      }),
    });
  });
va.displayName = "@mantine/core/CheckboxCard";
va.classes = qd;
function Qv({ children: e, role: t }) {
  const n = br();
  return n
    ? k.jsx("div", {
        role: t,
        "aria-labelledby": n.labelId,
        "aria-describedby": n.describedBy,
        children: e,
      })
    : k.jsx(k.Fragment, { children: e });
}
const Gv = {},
  ga = Ce((e, t) => {
    const {
        value: n,
        defaultValue: r,
        onChange: o,
        size: i,
        wrapperProps: l,
        children: s,
        readOnly: a,
        ...u
      } = H("CheckboxGroup", Gv, e),
      [f, d] = ry({ value: n, defaultValue: r, finalValue: [], onChange: o }),
      h = (g) => {
        const y = typeof g == "string" ? g : g.currentTarget.value;
        !a && d(f.includes(y) ? f.filter((v) => v !== y) : [...f, y]);
      };
    return k.jsx(Bv, {
      value: { value: f, onChange: h, size: i },
      children: k.jsx(ye.Wrapper, {
        size: i,
        ref: t,
        ...l,
        ...u,
        labelElement: "div",
        __staticSelector: "CheckboxGroup",
        children: k.jsx(Qv, { role: "group", children: s }),
      }),
    });
  });
ga.classes = ye.Wrapper.classes;
ga.displayName = "@mantine/core/CheckboxGroup";
function Yv({ size: e, style: t, ...n }) {
  const r = e !== void 0 ? { width: $(e), height: $(e), ...t } : t;
  return k.jsx("svg", {
    viewBox: "0 0 10 7",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
    style: r,
    "aria-hidden": !0,
    ...n,
    children: k.jsx("path", {
      d: "M4 4.586L1.707 2.293A1 1 0 1 0 .293 3.707l3 3a.997.997 0 0 0 1.414 0l5-5A1 1 0 1 0 8.293.293L4 4.586z",
      fill: "currentColor",
      fillRule: "evenodd",
      clipRule: "evenodd",
    }),
  });
}
function ep({ indeterminate: e, ...t }) {
  return e
    ? k.jsx("svg", {
        xmlns: "http://www.w3.org/2000/svg",
        fill: "none",
        viewBox: "0 0 32 6",
        "aria-hidden": !0,
        ...t,
        children: k.jsx("rect", {
          width: "32",
          height: "6",
          fill: "currentColor",
          rx: "3",
        }),
      })
    : k.jsx(Yv, { ...t });
}
var tp = {
  indicator: "m_5e5256ee",
  icon: "m_1b1c543a",
  "indicator--outline": "m_76e20374",
};
const Kv = { icon: ep },
  Xv = (
    e,
    { radius: t, color: n, size: r, iconColor: o, variant: i, autoContrast: l }
  ) => {
    const s = un({ color: n || e.primaryColor, theme: e }),
      a =
        s.isThemeColor && s.shade === void 0
          ? `var(--mantine-color-${s.color}-outline)`
          : s.color;
    return {
      indicator: {
        "--checkbox-size": Ye(r, "checkbox-size"),
        "--checkbox-radius": t === void 0 ? void 0 : Hr(t),
        "--checkbox-color": i === "outline" ? a : Ut(n, e),
        "--checkbox-icon-color": o
          ? Ut(o, e)
          : Od(l, e)
          ? ua({ color: n, theme: e, autoContrast: l })
          : void 0,
      },
    };
  },
  wa = Ce((e, t) => {
    const n = H("CheckboxIndicator", Kv, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        icon: u,
        indeterminate: f,
        radius: d,
        color: h,
        iconColor: g,
        autoContrast: y,
        checked: v,
        mod: C,
        variant: m,
        disabled: c,
        ...p
      } = n,
      S = u,
      _ = ue({
        name: "CheckboxIndicator",
        classes: tp,
        props: n,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        vars: a,
        varsResolver: Xv,
        rootSelector: "indicator",
      }),
      w = Uv(),
      E =
        typeof v == "boolean" || typeof f == "boolean"
          ? v || f
          : (w == null ? void 0 : w.checked) || !1;
    return k.jsx(V, {
      ref: t,
      ..._("indicator", { variant: m }),
      variant: m,
      mod: [{ checked: E, disabled: c }, C],
      ...p,
      children: k.jsx(S, { indeterminate: f, ..._("icon") }),
    });
  });
wa.displayName = "@mantine/core/CheckboxIndicator";
wa.classes = tp;
var np = {
  root: "m_bf2d988c",
  inner: "m_26062bec",
  input: "m_26063560",
  icon: "m_bf295423",
  "input--outline": "m_215c4542",
};
const Zv = { labelPosition: "right", icon: ep },
  Jv = (
    e,
    { radius: t, color: n, size: r, iconColor: o, variant: i, autoContrast: l }
  ) => {
    const s = un({ color: n || e.primaryColor, theme: e }),
      a =
        s.isThemeColor && s.shade === void 0
          ? `var(--mantine-color-${s.color}-outline)`
          : s.color;
    return {
      root: {
        "--checkbox-size": Ye(r, "checkbox-size"),
        "--checkbox-radius": t === void 0 ? void 0 : Hr(t),
        "--checkbox-color": i === "outline" ? a : Ut(n, e),
        "--checkbox-icon-color": o
          ? Ut(o, e)
          : Od(l, e)
          ? ua({ color: n, theme: e, autoContrast: l })
          : void 0,
      },
    };
  },
  bn = Ce((e, t) => {
    const n = H("Checkbox", Zv, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        color: u,
        label: f,
        id: d,
        size: h,
        radius: g,
        wrapperProps: y,
        checked: v,
        labelPosition: C,
        description: m,
        error: c,
        disabled: p,
        variant: S,
        indeterminate: _,
        icon: w,
        rootRef: E,
        iconColor: N,
        onChange: I,
        autoContrast: O,
        mod: b,
        ...ie
      } = n,
      W = Jd(),
      le = h || (W == null ? void 0 : W.size),
      Xe = w,
      ce = ue({
        name: "Checkbox",
        props: n,
        classes: np,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        vars: a,
        varsResolver: Jv,
      }),
      { styleProps: je, rest: T } = pi(ie),
      L = Pd(d),
      z = W
        ? {
            checked: W.value.includes(T.value),
            onChange: (j) => {
              W.onChange(j), I == null || I(j);
            },
          }
        : {};
    return k.jsx(Xd, {
      ...ce("root"),
      __staticSelector: "Checkbox",
      __stylesApiProps: n,
      id: L,
      size: le,
      labelPosition: C,
      label: f,
      description: m,
      error: c,
      disabled: p,
      classNames: r,
      styles: l,
      unstyled: s,
      "data-checked": z.checked || v || void 0,
      variant: S,
      ref: E,
      mod: b,
      ...je,
      ...y,
      children: k.jsxs(V, {
        ...ce("inner"),
        mod: { "data-label-position": C },
        children: [
          k.jsx(V, {
            component: "input",
            id: L,
            ref: t,
            checked: v,
            disabled: p,
            mod: { error: !!c, indeterminate: _ },
            ...ce("input", { focusable: !0, variant: S }),
            onChange: I,
            ...T,
            ...z,
            type: "checkbox",
          }),
          k.jsx(Xe, { indeterminate: _, ...ce("icon") }),
        ],
      }),
    });
  });
bn.classes = { ...np, ...Av };
bn.displayName = "@mantine/core/Checkbox";
bn.Group = ga;
bn.Indicator = wa;
bn.Card = va;
var Si = {
  root: "m_77c9d27d",
  inner: "m_80f1301b",
  label: "m_811560b9",
  section: "m_a74036a",
  loader: "m_a25b86ee",
  group: "m_80d6d844",
};
const Qu = { orientation: "horizontal" },
  qv = (e, { borderWidth: t }) => ({
    group: { "--button-border-width": $(t) },
  }),
  Sa = Ce((e, t) => {
    const n = H("ButtonGroup", Qu, e),
      {
        className: r,
        style: o,
        classNames: i,
        styles: l,
        unstyled: s,
        orientation: a,
        vars: u,
        borderWidth: f,
        variant: d,
        mod: h,
        ...g
      } = H("ButtonGroup", Qu, e),
      y = ue({
        name: "ButtonGroup",
        props: n,
        classes: Si,
        className: r,
        style: o,
        classNames: i,
        styles: l,
        unstyled: s,
        vars: u,
        varsResolver: qv,
        rootSelector: "group",
      });
    return k.jsx(V, {
      ...y("group"),
      ref: t,
      variant: d,
      mod: [{ "data-orientation": a }, h],
      role: "group",
      ...g,
    });
  });
Sa.classes = Si;
Sa.displayName = "@mantine/core/ButtonGroup";
const e0 = {
    in: { opacity: 1, transform: `translate(-50%, calc(-50% + ${$(1)}))` },
    out: { opacity: 0, transform: "translate(-50%, -200%)" },
    common: { transformOrigin: "center" },
    transitionProperty: "transform, opacity",
  },
  t0 = {},
  n0 = (
    e,
    {
      radius: t,
      color: n,
      gradient: r,
      variant: o,
      size: i,
      justify: l,
      autoContrast: s,
    }
  ) => {
    const a = e.variantColorResolver({
      color: n || e.primaryColor,
      theme: e,
      gradient: r,
      variant: o || "filled",
      autoContrast: s,
    });
    return {
      root: {
        "--button-justify": l,
        "--button-height": Ye(i, "button-height"),
        "--button-padding-x": Ye(i, "button-padding-x"),
        "--button-fz":
          i != null && i.includes("compact")
            ? it(i.replace("compact-", ""))
            : it(i),
        "--button-radius": t === void 0 ? void 0 : Hr(t),
        "--button-bg": n || o ? a.background : void 0,
        "--button-hover": n || o ? a.hover : void 0,
        "--button-color": a.color,
        "--button-bd": n || o ? a.border : void 0,
        "--button-hover-color": n || o ? a.hoverColor : void 0,
      },
    };
  },
  Mr = Hn((e, t) => {
    const n = H("Button", t0, e),
      {
        style: r,
        vars: o,
        className: i,
        color: l,
        disabled: s,
        children: a,
        leftSection: u,
        rightSection: f,
        fullWidth: d,
        variant: h,
        radius: g,
        loading: y,
        loaderProps: v,
        gradient: C,
        classNames: m,
        styles: c,
        unstyled: p,
        "data-disabled": S,
        autoContrast: _,
        mod: w,
        ...E
      } = n,
      N = ue({
        name: "Button",
        props: n,
        classes: Si,
        className: i,
        style: r,
        classNames: m,
        styles: c,
        unstyled: p,
        vars: o,
        varsResolver: n0,
      }),
      I = !!u,
      O = !!f;
    return k.jsxs(mi, {
      ref: t,
      ...N("root", { active: !s && !y && !S }),
      unstyled: p,
      variant: h,
      disabled: s || y,
      mod: [
        {
          disabled: s || S,
          loading: y,
          block: d,
          "with-left-section": I,
          "with-right-section": O,
        },
        w,
      ],
      ...E,
      children: [
        k.jsx(Bd, {
          mounted: !!y,
          transition: e0,
          duration: 150,
          children: (b) =>
            k.jsx(V, {
              component: "span",
              ...N("loader", { style: b }),
              "aria-hidden": !0,
              children: k.jsx(hi, {
                color: "var(--button-color)",
                size: "calc(var(--button-height) / 1.8)",
                ...v,
              }),
            }),
        }),
        k.jsxs("span", {
          ...N("inner"),
          children: [
            u &&
              k.jsx(V, {
                component: "span",
                ...N("section"),
                mod: { position: "left" },
                children: u,
              }),
            k.jsx(V, {
              component: "span",
              mod: { loading: y },
              ...N("label"),
              children: a,
            }),
            f &&
              k.jsx(V, {
                component: "span",
                ...N("section"),
                mod: { position: "right" },
                children: f,
              }),
          ],
        }),
      ],
    });
  });
Mr.classes = Si;
Mr.displayName = "@mantine/core/Button";
Mr.Group = Sa;
const [Gu, rp] = Gh("Grid component was not found in tree"),
  ts = (e, t) =>
    e === "content"
      ? "auto"
      : e === "auto"
      ? "0rem"
      : e
      ? `${100 / (t / e)}%`
      : void 0,
  Yu = (e, t, n) =>
    n || e === "auto" ? "100%" : e === "content" ? "unset" : ts(e, t),
  Ku = (e, t) => {
    if (e) return e === "auto" || t ? "1" : "auto";
  },
  Xu = (e, t) => (e === 0 ? "0" : e ? `${100 / (t / e)}%` : void 0);
function r0({ span: e, order: t, offset: n, selector: r }) {
  var g;
  const o = Et(),
    i = rp(),
    l = i.breakpoints || o.breakpoints,
    a = ar(e) === void 0 ? 12 : ar(e),
    u = Ur({
      "--col-order": (g = ar(t)) == null ? void 0 : g.toString(),
      "--col-flex-grow": Ku(a, i.grow),
      "--col-flex-basis": ts(a, i.columns),
      "--col-width": a === "content" ? "auto" : void 0,
      "--col-max-width": Yu(a, i.columns, i.grow),
      "--col-offset": Xu(ar(n), i.columns),
    }),
    f = ke(l).reduce((y, v) => {
      var C;
      return (
        y[v] || (y[v] = {}),
        typeof t == "object" &&
          t[v] !== void 0 &&
          (y[v]["--col-order"] = (C = t[v]) == null ? void 0 : C.toString()),
        typeof e == "object" &&
          e[v] !== void 0 &&
          ((y[v]["--col-flex-grow"] = Ku(e[v], i.grow)),
          (y[v]["--col-flex-basis"] = ts(e[v], i.columns)),
          (y[v]["--col-width"] = e[v] === "content" ? "auto" : void 0),
          (y[v]["--col-max-width"] = Yu(e[v], i.columns, i.grow))),
        typeof n == "object" &&
          n[v] !== void 0 &&
          (y[v]["--col-offset"] = Xu(n[v], i.columns)),
        y
      );
    }, {}),
    h = Nd(ke(f), l)
      .filter((y) => ke(f[y.value]).length > 0)
      .map((y) => ({
        query:
          i.type === "container"
            ? `mantine-grid (min-width: ${l[y.value]})`
            : `(min-width: ${l[y.value]})`,
        styles: f[y.value],
      }));
  return k.jsx(ca, {
    styles: u,
    media: i.type === "container" ? void 0 : h,
    container: i.type === "container" ? h : void 0,
    selector: r,
  });
}
var ka = {
  container: "m_8478a6da",
  root: "m_410352e9",
  inner: "m_dee7bd2f",
  col: "m_96bdd299",
};
const o0 = { span: 12 },
  xa = Ce((e, t) => {
    const n = H("GridCol", o0, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        vars: s,
        span: a,
        order: u,
        offset: f,
        ...d
      } = n,
      h = rp(),
      g = da();
    return k.jsxs(k.Fragment, {
      children: [
        k.jsx(r0, { selector: `.${g}`, span: a, order: u, offset: f }),
        k.jsx(V, {
          ref: t,
          ...h.getStyles("col", {
            className: Ct(o, g),
            style: i,
            classNames: r,
            styles: l,
          }),
          ...d,
        }),
      ],
    });
  });
xa.classes = ka;
xa.displayName = "@mantine/core/GridCol";
function Zu({ gutter: e, selector: t, breakpoints: n, type: r }) {
  const o = Et(),
    i = n || o.breakpoints,
    l = Ur({ "--grid-gutter": Or(ar(e)) }),
    s = ke(i).reduce(
      (f, d) => (
        f[d] || (f[d] = {}),
        typeof e == "object" &&
          e[d] !== void 0 &&
          (f[d]["--grid-gutter"] = Or(e[d])),
        f
      ),
      {}
    ),
    u = Nd(ke(s), i)
      .filter((f) => ke(s[f.value]).length > 0)
      .map((f) => ({
        query:
          r === "container"
            ? `mantine-grid (min-width: ${i[f.value]})`
            : `(min-width: ${i[f.value]})`,
        styles: s[f.value],
      }));
  return k.jsx(ca, {
    styles: l,
    media: r === "container" ? void 0 : u,
    container: r === "container" ? u : void 0,
    selector: t,
  });
}
const i0 = { gutter: "md", grow: !1, columns: 12 },
  l0 = (e, { justify: t, align: n, overflow: r }) => ({
    root: { "--grid-justify": t, "--grid-align": n, "--grid-overflow": r },
  }),
  Ln = Ce((e, t) => {
    const n = H("Grid", i0, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        grow: u,
        gutter: f,
        columns: d,
        align: h,
        justify: g,
        children: y,
        breakpoints: v,
        type: C,
        ...m
      } = n,
      c = ue({
        name: "Grid",
        classes: ka,
        props: n,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        vars: a,
        varsResolver: l0,
      }),
      p = da();
    return C === "container" && v
      ? k.jsxs(Gu, {
          value: {
            getStyles: c,
            grow: u,
            columns: d || 12,
            breakpoints: v,
            type: C,
          },
          children: [
            k.jsx(Zu, { selector: `.${p}`, ...n }),
            k.jsx("div", {
              ...c("container"),
              children: k.jsx(V, {
                ref: t,
                ...c("root", { className: p }),
                ...m,
                children: k.jsx("div", { ...c("inner"), children: y }),
              }),
            }),
          ],
        })
      : k.jsxs(Gu, {
          value: {
            getStyles: c,
            grow: u,
            columns: d || 12,
            breakpoints: v,
            type: C,
          },
          children: [
            k.jsx(Zu, { selector: `.${p}`, ...n }),
            k.jsx(V, {
              ref: t,
              ...c("root", { className: p }),
              ...m,
              children: k.jsx("div", { ...c("inner"), children: y }),
            }),
          ],
        });
  });
Ln.classes = ka;
Ln.displayName = "@mantine/core/Grid";
Ln.Col = xa;
function ns() {
  return (
    (ns = Object.assign
      ? Object.assign.bind()
      : function (e) {
          for (var t = 1; t < arguments.length; t++) {
            var n = arguments[t];
            for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
          }
          return e;
        }),
    ns.apply(null, arguments)
  );
}
function s0(e, t) {
  if (e == null) return {};
  var n = {};
  for (var r in e)
    if ({}.hasOwnProperty.call(e, r)) {
      if (t.includes(r)) continue;
      n[r] = e[r];
    }
  return n;
}
var a0 = x.useLayoutEffect,
  u0 = function (t) {
    var n = x.useRef(t);
    return (
      a0(function () {
        n.current = t;
      }),
      n
    );
  },
  Ju = function (t, n) {
    if (typeof t == "function") {
      t(n);
      return;
    }
    t.current = n;
  },
  c0 = function (t, n) {
    var r = x.useRef();
    return x.useCallback(
      function (o) {
        (t.current = o),
          r.current && Ju(r.current, null),
          (r.current = n),
          n && Ju(n, o);
      },
      [n]
    );
  },
  qu = {
    "min-height": "0",
    "max-height": "none",
    height: "0",
    visibility: "hidden",
    overflow: "hidden",
    position: "absolute",
    "z-index": "-1000",
    top: "0",
    right: "0",
  },
  f0 = function (t) {
    Object.keys(qu).forEach(function (n) {
      t.style.setProperty(n, qu[n], "important");
    });
  },
  ec = f0,
  Ee = null,
  tc = function (t, n) {
    var r = t.scrollHeight;
    return n.sizingStyle.boxSizing === "border-box"
      ? r + n.borderSize
      : r - n.paddingSize;
  };
function d0(e, t, n, r) {
  n === void 0 && (n = 1),
    r === void 0 && (r = 1 / 0),
    Ee ||
      ((Ee = document.createElement("textarea")),
      Ee.setAttribute("tabindex", "-1"),
      Ee.setAttribute("aria-hidden", "true"),
      ec(Ee)),
    Ee.parentNode === null && document.body.appendChild(Ee);
  var o = e.paddingSize,
    i = e.borderSize,
    l = e.sizingStyle,
    s = l.boxSizing;
  Object.keys(l).forEach(function (h) {
    var g = h;
    Ee.style[g] = l[g];
  }),
    ec(Ee),
    (Ee.value = t);
  var a = tc(Ee, e);
  (Ee.value = t), (a = tc(Ee, e)), (Ee.value = "x");
  var u = Ee.scrollHeight - o,
    f = u * n;
  s === "border-box" && (f = f + o + i), (a = Math.max(f, a));
  var d = u * r;
  return s === "border-box" && (d = d + o + i), (a = Math.min(d, a)), [a, u];
}
var nc = function () {},
  p0 = function (t, n) {
    return t.reduce(function (r, o) {
      return (r[o] = n[o]), r;
    }, {});
  },
  m0 = [
    "borderBottomWidth",
    "borderLeftWidth",
    "borderRightWidth",
    "borderTopWidth",
    "boxSizing",
    "fontFamily",
    "fontSize",
    "fontStyle",
    "fontWeight",
    "letterSpacing",
    "lineHeight",
    "paddingBottom",
    "paddingLeft",
    "paddingRight",
    "paddingTop",
    "tabSize",
    "textIndent",
    "textRendering",
    "textTransform",
    "width",
    "wordBreak",
  ],
  h0 = !!document.documentElement.currentStyle,
  y0 = function (t) {
    var n = window.getComputedStyle(t);
    if (n === null) return null;
    var r = p0(m0, n),
      o = r.boxSizing;
    if (o === "") return null;
    h0 &&
      o === "border-box" &&
      (r.width =
        parseFloat(r.width) +
        parseFloat(r.borderRightWidth) +
        parseFloat(r.borderLeftWidth) +
        parseFloat(r.paddingRight) +
        parseFloat(r.paddingLeft) +
        "px");
    var i = parseFloat(r.paddingBottom) + parseFloat(r.paddingTop),
      l = parseFloat(r.borderBottomWidth) + parseFloat(r.borderTopWidth);
    return { sizingStyle: r, paddingSize: i, borderSize: l };
  },
  v0 = y0;
function op(e, t, n) {
  var r = u0(n);
  x.useLayoutEffect(function () {
    var o = function (l) {
      return r.current(l);
    };
    if (e)
      return (
        e.addEventListener(t, o),
        function () {
          return e.removeEventListener(t, o);
        }
      );
  }, []);
}
var g0 = function (t) {
    op(window, "resize", t);
  },
  w0 = function (t) {
    op(document.fonts, "loadingdone", t);
  },
  S0 = [
    "cacheMeasurements",
    "maxRows",
    "minRows",
    "onChange",
    "onHeightChange",
  ],
  k0 = function (t, n) {
    var r = t.cacheMeasurements,
      o = t.maxRows,
      i = t.minRows,
      l = t.onChange,
      s = l === void 0 ? nc : l,
      a = t.onHeightChange,
      u = a === void 0 ? nc : a,
      f = s0(t, S0),
      d = f.value !== void 0,
      h = x.useRef(null),
      g = c0(h, n),
      y = x.useRef(0),
      v = x.useRef(),
      C = function () {
        var p = h.current,
          S = r && v.current ? v.current : v0(p);
        if (S) {
          v.current = S;
          var _ = d0(S, p.value || p.placeholder || "x", i, o),
            w = _[0],
            E = _[1];
          y.current !== w &&
            ((y.current = w),
            p.style.setProperty("height", w + "px", "important"),
            u(w, { rowHeight: E }));
        }
      },
      m = function (p) {
        d || C(), s(p);
      };
    return (
      x.useLayoutEffect(C),
      g0(C),
      w0(C),
      x.createElement("textarea", ns({}, f, { onChange: m, ref: g }))
    );
  },
  x0 = x.forwardRef(k0);
const C0 = {},
  Ca = Ce((e, t) => {
    const {
        autosize: n,
        maxRows: r,
        minRows: o,
        __staticSelector: i,
        resize: l,
        ...s
      } = H("Textarea", C0, e),
      a = n && ly() !== "test",
      u = a ? { maxRows: r, minRows: o } : {};
    return k.jsx(wi, {
      component: a ? x0 : "textarea",
      ref: t,
      ...s,
      __staticSelector: i || "Textarea",
      multiline: !0,
      "data-no-overflow": (n && r === void 0) || void 0,
      __vars: { "--input-resize": l },
      ...u,
    });
  });
Ca.classes = wi.classes;
Ca.displayName = "@mantine/core/Textarea";
var ip = { root: "m_6d731127" };
const E0 = { gap: "md", align: "stretch", justify: "flex-start" },
  _0 = (e, { gap: t, align: n, justify: r }) => ({
    root: { "--stack-gap": Or(t), "--stack-align": n, "--stack-justify": r },
  }),
  ki = Ce((e, t) => {
    const n = H("Stack", E0, e),
      {
        classNames: r,
        className: o,
        style: i,
        styles: l,
        unstyled: s,
        vars: a,
        align: u,
        justify: f,
        gap: d,
        variant: h,
        ...g
      } = n,
      y = ue({
        name: "Stack",
        props: n,
        classes: ip,
        className: o,
        style: i,
        classNames: r,
        styles: l,
        unstyled: s,
        vars: a,
        varsResolver: _0,
      });
    return k.jsx(V, { ref: t, ...y("root"), variant: h, ...g });
  });
ki.classes = ip;
ki.displayName = "@mantine/core/Stack";
function $0(e) {
  if (!/^[0-9a-zA-Z-]+$/.test(e))
    throw new Error(
      `[@mantine/use-form] Form name "${e}" is invalid, it should contain only letters, numbers and dashes`
    );
}
const N0 = typeof window < "u" ? x.useLayoutEffect : x.useEffect;
function de(e, t) {
  N0(() => {
    if (e)
      return (
        window.addEventListener(e, t), () => window.removeEventListener(e, t)
      );
  }, [e]);
}
function P0(e, t) {
  e && $0(e),
    de(`mantine-form:${e}:set-field-value`, (n) =>
      t.setFieldValue(n.detail.path, n.detail.value)
    ),
    de(`mantine-form:${e}:set-values`, (n) => t.setValues(n.detail)),
    de(`mantine-form:${e}:set-initial-values`, (n) =>
      t.setInitialValues(n.detail)
    ),
    de(`mantine-form:${e}:set-errors`, (n) => t.setErrors(n.detail)),
    de(`mantine-form:${e}:set-field-error`, (n) =>
      t.setFieldError(n.detail.path, n.detail.error)
    ),
    de(`mantine-form:${e}:clear-field-error`, (n) =>
      t.clearFieldError(n.detail)
    ),
    de(`mantine-form:${e}:clear-errors`, t.clearErrors),
    de(`mantine-form:${e}:reset`, t.reset),
    de(`mantine-form:${e}:validate`, t.validate),
    de(`mantine-form:${e}:validate-field`, (n) => t.validateField(n.detail)),
    de(`mantine-form:${e}:reorder-list-item`, (n) =>
      t.reorderListItem(n.detail.path, n.detail.payload)
    ),
    de(`mantine-form:${e}:remove-list-item`, (n) =>
      t.removeListItem(n.detail.path, n.detail.index)
    ),
    de(`mantine-form:${e}:insert-list-item`, (n) =>
      t.insertListItem(n.detail.path, n.detail.item, n.detail.index)
    ),
    de(`mantine-form:${e}:set-dirty`, (n) => t.setDirty(n.detail)),
    de(`mantine-form:${e}:set-touched`, (n) => t.setTouched(n.detail)),
    de(`mantine-form:${e}:reset-dirty`, (n) => t.resetDirty(n.detail)),
    de(`mantine-form:${e}:reset-touched`, t.resetTouched);
}
function j0(e) {
  return (t) => {
    if (!t) e(t);
    else if (typeof t == "function") e(t);
    else if (typeof t == "object" && "nativeEvent" in t) {
      const { currentTarget: n } = t;
      n instanceof HTMLInputElement
        ? n.type === "checkbox"
          ? e(n.checked)
          : e(n.value)
        : (n instanceof HTMLTextAreaElement ||
            n instanceof HTMLSelectElement) &&
          e(n.value);
    } else e(t);
  };
}
function rs(e) {
  return e === null || typeof e != "object"
    ? {}
    : Object.keys(e).reduce((t, n) => {
        const r = e[n];
        return r != null && r !== !1 && (t[n] = r), t;
      }, {});
}
function T0(e) {
  const [t, n] = x.useState(rs(e)),
    r = x.useRef(t),
    o = x.useCallback((a) => {
      n((u) => {
        const f = rs(typeof a == "function" ? a(u) : a);
        return (r.current = f), f;
      });
    }, []),
    i = x.useCallback(() => o({}), []),
    l = x.useCallback(
      (a) => {
        r.current[a] !== void 0 &&
          o((u) => {
            const f = { ...u };
            return delete f[a], f;
          });
      },
      [t]
    ),
    s = x.useCallback(
      (a, u) => {
        u == null || u === !1
          ? l(a)
          : r.current[a] !== u && o((f) => ({ ...f, [a]: u }));
      },
      [t]
    );
  return {
    errorsState: t,
    setErrors: o,
    clearErrors: i,
    setFieldError: s,
    clearFieldError: l,
  };
}
function os(e, t) {
  if (t === null || typeof t != "object") return {};
  const n = { ...t };
  return (
    Object.keys(t).forEach((r) => {
      r.includes(`${String(e)}.`) && delete n[r];
    }),
    n
  );
}
function rc(e, t) {
  const n = e.substring(t.length + 1).split(".")[0];
  return parseInt(n, 10);
}
function oc(e, t, n, r) {
  if (t === void 0) return n;
  const o = `${String(e)}`;
  let i = n;
  r === -1 && (i = os(`${o}.${t}`, i));
  const l = { ...i },
    s = new Set();
  return (
    Object.entries(i)
      .filter(([a]) => {
        if (!a.startsWith(`${o}.`)) return !1;
        const u = rc(a, o);
        return Number.isNaN(u) ? !1 : u >= t;
      })
      .forEach(([a, u]) => {
        const f = rc(a, o),
          d = a.replace(`${o}.${f}`, `${o}.${f + r}`);
        (l[d] = u), s.add(d), s.has(a) || delete l[a];
      }),
    l
  );
}
function R0(e, { from: t, to: n }, r) {
  const o = `${e}.${t}`,
    i = `${e}.${n}`,
    l = { ...r };
  return (
    Object.keys(r).every((s) => {
      let a, u;
      if (
        (s.startsWith(o) && ((a = s), (u = s.replace(o, i))),
        s.startsWith(i) && ((a = s.replace(i, o)), (u = s)),
        a && u)
      ) {
        const f = l[a],
          d = l[u];
        return (
          d === void 0 ? delete l[a] : (l[a] = d),
          f === void 0 ? delete l[u] : (l[u] = f),
          !1
        );
      }
      return !0;
    }),
    l
  );
}
function ic(e, t, n) {
  typeof n.value == "object" && (n.value = $n(n.value)),
    !n.enumerable ||
    n.get ||
    n.set ||
    !n.configurable ||
    !n.writable ||
    t === "__proto__"
      ? Object.defineProperty(e, t, n)
      : (e[t] = n.value);
}
function $n(e) {
  if (typeof e != "object") return e;
  var t = 0,
    n,
    r,
    o,
    i = Object.prototype.toString.call(e);
  if (
    (i === "[object Object]"
      ? (o = Object.create(e.__proto__ || null))
      : i === "[object Array]"
      ? (o = Array(e.length))
      : i === "[object Set]"
      ? ((o = new Set()),
        e.forEach(function (l) {
          o.add($n(l));
        }))
      : i === "[object Map]"
      ? ((o = new Map()),
        e.forEach(function (l, s) {
          o.set($n(s), $n(l));
        }))
      : i === "[object Date]"
      ? (o = new Date(+e))
      : i === "[object RegExp]"
      ? (o = new RegExp(e.source, e.flags))
      : i === "[object DataView]"
      ? (o = new e.constructor($n(e.buffer)))
      : i === "[object ArrayBuffer]"
      ? (o = e.slice(0))
      : i.slice(-6) === "Array]" && (o = new e.constructor(e)),
    o)
  ) {
    for (r = Object.getOwnPropertySymbols(e); t < r.length; t++)
      ic(o, r[t], Object.getOwnPropertyDescriptor(e, r[t]));
    for (t = 0, r = Object.getOwnPropertyNames(e); t < r.length; t++)
      (Object.hasOwnProperty.call(o, (n = r[t])) && o[n] === e[n]) ||
        ic(o, n, Object.getOwnPropertyDescriptor(e, n));
  }
  return o || e;
}
function lp(e) {
  return typeof e != "string" ? [] : e.split(".");
}
function Se(e, t) {
  const n = lp(e);
  if (n.length === 0 || typeof t != "object" || t === null) return;
  let r = t[n[0]];
  for (let o = 1; o < n.length && r != null; o += 1) r = r[n[o]];
  return r;
}
function xi(e, t, n) {
  const r = lp(e);
  if (r.length === 0) return n;
  const o = $n(n);
  if (r.length === 1) return (o[r[0]] = t), o;
  let i = o[r[0]];
  for (let l = 1; l < r.length - 1; l += 1) {
    if (i === void 0) return o;
    i = i[r[l]];
  }
  return (i[r[r.length - 1]] = t), o;
}
function z0(e, { from: t, to: n }, r) {
  const o = Se(e, r);
  if (!Array.isArray(o)) return r;
  const i = [...o],
    l = o[t];
  return i.splice(t, 1), i.splice(n, 0, l), xi(e, i, r);
}
function L0(e, t, n, r) {
  const o = Se(e, r);
  if (!Array.isArray(o)) return r;
  const i = [...o];
  return i.splice(typeof n == "number" ? n : i.length, 0, t), xi(e, i, r);
}
function I0(e, t, n) {
  const r = Se(e, n);
  return Array.isArray(r)
    ? xi(
        e,
        r.filter((o, i) => i !== t),
        n
      )
    : n;
}
function O0({ $values: e, $errors: t, $status: n }) {
  const r = x.useCallback((l, s) => {
      n.clearFieldDirty(l),
        t.setErrors((a) => R0(l, s, a)),
        e.setValues({ values: z0(l, s, e.refValues.current), updateState: !0 });
    }, []),
    o = x.useCallback((l, s) => {
      n.clearFieldDirty(l),
        t.setErrors((a) => oc(l, s, a, -1)),
        e.setValues({ values: I0(l, s, e.refValues.current), updateState: !0 });
    }, []),
    i = x.useCallback((l, s, a) => {
      n.clearFieldDirty(l),
        t.setErrors((u) => oc(l, a, u, 1)),
        e.setValues({
          values: L0(l, s, a, e.refValues.current),
          updateState: !0,
        });
    }, []);
  return { reorderListItem: r, removeListItem: o, insertListItem: i };
}
var F0 = function e(t, n) {
  if (t === n) return !0;
  if (t && n && typeof t == "object" && typeof n == "object") {
    if (t.constructor !== n.constructor) return !1;
    var r, o, i;
    if (Array.isArray(t)) {
      if (((r = t.length), r != n.length)) return !1;
      for (o = r; o-- !== 0; ) if (!e(t[o], n[o])) return !1;
      return !0;
    }
    if (t.constructor === RegExp)
      return t.source === n.source && t.flags === n.flags;
    if (t.valueOf !== Object.prototype.valueOf)
      return t.valueOf() === n.valueOf();
    if (t.toString !== Object.prototype.toString)
      return t.toString() === n.toString();
    if (((i = Object.keys(t)), (r = i.length), r !== Object.keys(n).length))
      return !1;
    for (o = r; o-- !== 0; )
      if (!Object.prototype.hasOwnProperty.call(n, i[o])) return !1;
    for (o = r; o-- !== 0; ) {
      var l = i[o];
      if (!e(t[l], n[l])) return !1;
    }
    return !0;
  }
  return t !== t && n !== n;
};
const po = ss(F0);
function rr(e, t) {
  const n = Object.keys(e);
  if (typeof t == "string") {
    const r = n.filter((o) => o.startsWith(`${t}.`));
    return e[t] || r.some((o) => e[o]) || !1;
  }
  return n.some((r) => e[r]);
}
function M0({ initialDirty: e, initialTouched: t, mode: n, $values: r }) {
  const [o, i] = x.useState(t),
    [l, s] = x.useState(e),
    a = x.useRef(t),
    u = x.useRef(e),
    f = x.useCallback((w) => {
      const E = typeof w == "function" ? w(a.current) : w;
      (a.current = E), n === "controlled" && i(E);
    }, []),
    d = x.useCallback((w, E = !1) => {
      const N = typeof w == "function" ? w(u.current) : w;
      (u.current = N), (n === "controlled" || E) && s(N);
    }, []),
    h = x.useCallback(() => f({}), []),
    g = (w) => {
      const E = w ? { ...w, ...r.refValues.current } : r.refValues.current;
      r.setValuesSnapshot(E), d({});
    },
    y = x.useCallback((w, E) => {
      f((N) => (rr(N, w) === E ? N : { ...N, [w]: E }));
    }, []),
    v = x.useCallback((w, E, N) => {
      d((I) => (rr(I, w) === E ? I : { ...I, [w]: E }), N);
    }, []),
    C = x.useCallback((w, E) => {
      const N = rr(u.current, w),
        I = !po(Se(w, r.getValuesSnapshot()), E),
        O = os(w, u.current);
      (O[w] = I), d(O, N !== I);
    }, []),
    m = x.useCallback((w) => rr(a.current, w), []),
    c = x.useCallback(
      (w) =>
        d((E) => {
          if (typeof w != "string") return E;
          const N = os(w, E);
          return delete N[w], po(N, E) ? E : N;
        }),
      []
    ),
    p = x.useCallback((w) => {
      if (w) {
        const N = Se(w, u.current);
        if (typeof N == "boolean") return N;
        const I = Se(w, r.refValues.current),
          O = Se(w, r.valuesSnapshot.current);
        return !po(I, O);
      }
      return Object.keys(u.current).length > 0
        ? rr(u.current)
        : !po(r.refValues.current, r.valuesSnapshot.current);
    }, []),
    S = x.useCallback(() => u.current, []),
    _ = x.useCallback(() => a.current, []);
  return {
    touchedState: o,
    dirtyState: l,
    touchedRef: a,
    dirtyRef: u,
    setTouched: f,
    setDirty: d,
    resetDirty: g,
    resetTouched: h,
    isTouched: m,
    setFieldTouched: y,
    setFieldDirty: v,
    setTouchedState: i,
    setDirtyState: s,
    clearFieldDirty: c,
    isDirty: p,
    getDirty: S,
    getTouched: _,
    setCalculatedFieldDirty: C,
  };
}
function D0({ initialValues: e, onValuesChange: t, mode: n }) {
  const r = x.useRef(!1),
    [o, i] = x.useState(e || {}),
    l = x.useRef(o),
    s = x.useRef(o),
    a = x.useCallback(
      ({
        values: v,
        subscribers: C,
        updateState: m = !0,
        mergeWithPreviousValues: c = !0,
      }) => {
        const p = l.current,
          S = v instanceof Function ? v(l.current) : v,
          _ = c ? { ...p, ...S } : S;
        (l.current = _),
          m && i(_),
          t == null || t(_, p),
          C == null ||
            C.filter(Boolean).forEach((w) =>
              w({ updatedValues: _, previousValues: p })
            );
      },
      [t]
    ),
    u = x.useCallback(
      (v) => {
        var c;
        const C = Se(v.path, l.current),
          m = v.value instanceof Function ? v.value(C) : v.value;
        if (C !== m) {
          const p = l.current,
            S = xi(v.path, m, l.current);
          a({ values: S, updateState: v.updateState }),
            (c = v.subscribers) == null ||
              c
                .filter(Boolean)
                .forEach((_) =>
                  _({ path: v.path, updatedValues: S, previousValues: p })
                );
        }
      },
      [a]
    ),
    f = x.useCallback((v) => {
      s.current = v;
    }, []),
    d = x.useCallback(
      (v, C) => {
        r.current ||
          ((r.current = !0),
          a({ values: v, updateState: n === "controlled" }),
          f(v),
          C());
      },
      [a]
    ),
    h = x.useCallback(() => {
      a({ values: s.current, updateState: !0, mergeWithPreviousValues: !1 });
    }, [a]),
    g = x.useCallback(() => l.current, []),
    y = x.useCallback(() => s.current, []);
  return {
    initialized: r,
    stateValues: o,
    refValues: l,
    valuesSnapshot: s,
    setValues: a,
    setFieldValue: u,
    resetValues: h,
    setValuesSnapshot: f,
    initialize: d,
    getValues: g,
    getValuesSnapshot: y,
  };
}
function V0({ $status: e }) {
  const t = x.useRef({}),
    n = x.useCallback((o, i) => {
      x.useEffect(
        () => (
          (t.current[o] = t.current[o] || []),
          t.current[o].push(i),
          () => {
            t.current[o] = t.current[o].filter((l) => l !== i);
          }
        ),
        [i]
      );
    }, []),
    r = x.useCallback(
      (o) =>
        t.current[o]
          ? t.current[o].map(
              (i) => (l) =>
                i({
                  previousValue: Se(o, l.previousValues),
                  value: Se(o, l.updatedValues),
                  touched: e.isTouched(o),
                  dirty: e.isDirty(o),
                })
            )
          : [],
      []
    );
  return { subscribers: t, watch: n, getFieldSubscribers: r };
}
function lc(e, t) {
  return e ? `${e}-${t.toString()}` : t.toString();
}
function sc(e) {
  const t = rs(e);
  return { hasErrors: Object.keys(t).length > 0, errors: t };
}
function is(e, t, n = "", r = {}) {
  return typeof e != "object" || e === null
    ? r
    : Object.keys(e).reduce((o, i) => {
        const l = e[i],
          s = `${n === "" ? "" : `${n}.`}${i}`,
          a = Se(s, t);
        let u = !1;
        return (
          typeof l == "function" && (o[s] = l(a, t, s)),
          typeof l == "object" &&
            Array.isArray(a) &&
            ((u = !0), a.forEach((f, d) => is(l, t, `${s}.${d}`, o))),
          typeof l == "object" &&
            typeof a == "object" &&
            a !== null &&
            (u || is(l, t, s, o)),
          o
        );
      }, r);
}
function ls(e, t) {
  return sc(typeof e == "function" ? e(t) : is(e, t));
}
function mo(e, t, n) {
  if (typeof e != "string") return { hasError: !1, error: null };
  const r = ls(t, n),
    o = Object.keys(r.errors).find((i) =>
      e.split(".").every((l, s) => l === i.split(".")[s])
    );
  return { hasError: !!o, error: o ? r.errors[o] : null };
}
const A0 = "__MANTINE_FORM_INDEX__";
function ac(e, t) {
  return t
    ? typeof t == "boolean"
      ? t
      : Array.isArray(t)
      ? t.includes(e.replace(/[.][0-9]+/g, `.${A0}`))
      : !1
    : !1;
}
function B0({
  name: e,
  mode: t = "controlled",
  initialValues: n,
  initialErrors: r = {},
  initialDirty: o = {},
  initialTouched: i = {},
  clearInputErrorOnChange: l = !0,
  validateInputOnChange: s = !1,
  validateInputOnBlur: a = !1,
  onValuesChange: u,
  transformValues: f = (g) => g,
  enhanceGetInputProps: d,
  validate: h,
} = {}) {
  const g = T0(r),
    y = D0({ initialValues: n, onValuesChange: u, mode: t }),
    v = M0({ initialDirty: o, initialTouched: i, $values: y, mode: t }),
    C = O0({ $values: y, $errors: g, $status: v }),
    m = V0({ $status: v }),
    [c, p] = x.useState(0),
    [S, _] = x.useState({}),
    w = x.useCallback(() => {
      y.resetValues(),
        g.clearErrors(),
        v.resetDirty(),
        v.resetTouched(),
        t === "uncontrolled" && p((j) => j + 1);
    }, []),
    E = x.useCallback(
      (j) => {
        l && g.clearErrors(),
          t === "uncontrolled" && p((F) => F + 1),
          Object.keys(m.subscribers.current).forEach((F) => {
            const B = Se(F, y.refValues.current),
              J = Se(F, j);
            B !== J &&
              m
                .getFieldSubscribers(F)
                .forEach((Oe) =>
                  Oe({ previousValues: j, updatedValues: y.refValues.current })
                );
          });
      },
      [l]
    ),
    N = x.useCallback(
      (j) => {
        const F = y.refValues.current;
        y.initialize(j, () => t === "uncontrolled" && p((B) => B + 1)), E(F);
      },
      [E]
    ),
    I = x.useCallback(
      (j, F, B) => {
        const J = ac(j, s),
          Oe = F instanceof Function ? F(Se(j, y.refValues.current)) : F;
        v.setCalculatedFieldDirty(j, Oe),
          v.setFieldTouched(j, !0),
          !J && l && g.clearFieldError(j),
          y.setFieldValue({
            path: j,
            value: F,
            updateState: t === "controlled",
            subscribers: [
              ...m.getFieldSubscribers(j),
              J
                ? (fe) => {
                    const ne = mo(j, h, fe.updatedValues);
                    ne.hasError
                      ? g.setFieldError(j, ne.error)
                      : g.clearFieldError(j);
                  }
                : null,
              (B == null ? void 0 : B.forceUpdate) !== !1 && t !== "controlled"
                ? () => _((fe) => ({ ...fe, [j]: (fe[j] || 0) + 1 }))
                : null,
            ],
          });
      },
      [u, h]
    ),
    O = x.useCallback(
      (j) => {
        const F = y.refValues.current;
        y.setValues({ values: j, updateState: t === "controlled" }), E(F);
      },
      [u, E]
    ),
    b = x.useCallback(() => {
      const j = ls(h, y.refValues.current);
      return g.setErrors(j.errors), j;
    }, [h]),
    ie = x.useCallback(
      (j) => {
        const F = mo(j, h, y.refValues.current);
        return (
          F.hasError ? g.setFieldError(j, F.error) : g.clearFieldError(j), F
        );
      },
      [h]
    ),
    W = (
      j,
      { type: F = "input", withError: B = !0, withFocus: J = !0, ...Oe } = {}
    ) => {
      const ne = {
        onChange: j0((_t) => I(j, _t, { forceUpdate: !1 })),
        "data-path": lc(e, j),
      };
      return (
        B && (ne.error = g.errorsState[j]),
        F === "checkbox"
          ? (ne[t === "controlled" ? "checked" : "defaultChecked"] = Se(
              j,
              y.refValues.current
            ))
          : (ne[t === "controlled" ? "value" : "defaultValue"] = Se(
              j,
              y.refValues.current
            )),
        J &&
          ((ne.onFocus = () => v.setFieldTouched(j, !0)),
          (ne.onBlur = () => {
            if (ac(j, a)) {
              const _t = mo(j, h, y.refValues.current);
              _t.hasError ? g.setFieldError(j, _t.error) : g.clearFieldError(j);
            }
          })),
        Object.assign(
          ne,
          d == null
            ? void 0
            : d({
                inputProps: ne,
                field: j,
                options: { type: F, withError: B, withFocus: J, ...Oe },
                form: z,
              })
        )
      );
    },
    le = (j, F) => (B) => {
      B == null || B.preventDefault();
      const J = b();
      J.hasErrors
        ? F == null || F(J.errors, y.refValues.current, B)
        : j == null || j(f(y.refValues.current), B);
    },
    Xe = (j) => f(j || y.refValues.current),
    ce = x.useCallback((j) => {
      j.preventDefault(), w();
    }, []),
    je = x.useCallback(
      (j) =>
        j
          ? !mo(j, h, y.refValues.current).hasError
          : !ls(h, y.refValues.current).hasErrors,
      [h]
    ),
    T = (j) => `${c}-${j}-${S[j] || 0}`,
    L = x.useCallback(
      (j) => document.querySelector(`[data-path="${lc(e, j)}"]`),
      []
    ),
    z = {
      watch: m.watch,
      initialized: y.initialized.current,
      values: y.stateValues,
      getValues: y.getValues,
      setInitialValues: y.setValuesSnapshot,
      initialize: N,
      setValues: O,
      setFieldValue: I,
      errors: g.errorsState,
      setErrors: g.setErrors,
      setFieldError: g.setFieldError,
      clearFieldError: g.clearFieldError,
      clearErrors: g.clearErrors,
      resetDirty: v.resetDirty,
      setTouched: v.setTouched,
      setDirty: v.setDirty,
      isTouched: v.isTouched,
      resetTouched: v.resetTouched,
      isDirty: v.isDirty,
      getTouched: v.getTouched,
      getDirty: v.getDirty,
      reorderListItem: C.reorderListItem,
      insertListItem: C.insertListItem,
      removeListItem: C.removeListItem,
      reset: w,
      validate: b,
      validateField: ie,
      getInputProps: W,
      onSubmit: le,
      onReset: ce,
      isValid: je,
      getTransformedValues: Xe,
      key: T,
      getInputNode: L,
    };
  return P0(e, z), z;
}
const sp = ({ node: e, level: t = 0, onCommandClick: n }) =>
    k.jsx(V, {
      pl: t * 16,
      className: t > 0 ? "tree-indent" : "",
      children: e.is_group
        ? k.jsxs(k.Fragment, {
            children: [
              k.jsx(tt, {
                className: "tree-group",
                mt: 4,
                mb: 4,
                children: e.name,
              }),
              k.jsx(ki, {
                spacing: 0,
                gap: "xs",
                children: e.children.map((r, o) =>
                  k.jsx(sp, { node: r, level: t + 1, onCommandClick: n }, o)
                ),
              }),
            ],
          })
        : k.jsx(ya, {
            href: "#",
            className: "tree-command",
            onClick: (r) => {
              r.preventDefault(), n(e);
            },
            children: k.jsx(tt, { mt: 2, mb: 2, children: e.name }),
          }),
    }),
  W0 = ({ tree: e, onCommandClick: t }) =>
    k.jsx(V, {
      className: "tree-view-container",
      children: k.jsx(sp, { node: e, onCommandClick: t }),
    }),
  U0 = () => {
    const [e, t] = x.useState({}),
      [n, r] = x.useState(null),
      [o, i] = x.useState("");
    x.useEffect(() => {
      const f = document.getElementById("tree");
      f && t(JSON.parse(f.textContent));
    }, []);
    const l = (f) => {
        r(f), i("");
      },
      s = B0({
        initialValues: n
          ? n.inputs.reduce((f, d) => ((f[d.name] = d.default || ""), f), {})
          : {},
      }),
      a = async (f) => {
        if ((f.preventDefault(), !n)) return;
        let d = { ...s.values };
        !n.endpoint.includes("/routes") &&
          !n.endpoint.includes("/app_metadata") &&
          (d.streaming = !0);
        const g = new URLSearchParams(d).toString(),
          y =
            n.endpoint.includes("/routes") ||
            n.endpoint.includes("/app_metadata"),
          v = y ? `${n.endpoint}?${g}` : n.endpoint;
        console.log(`🔹 Sending ${y ? "GET" : "POST"} request to: ${v}`), i("");
        try {
          const C = await fetch(v, {
            method: y ? "GET" : "POST",
            headers: { "Content-Type": "application/json" },
            body: y ? null : JSON.stringify(d),
          });
          if (!C.ok) throw new Error(`HTTP error! Status: ${C.status}`);
          const m = await C.text();
          console.log("🔹 Raw response from server:", m);
          let c;
          try {
            c = JSON.parse(m);
          } catch {
            console.warn("⚠️ Server returned plain text instead of JSON."),
              (c = m);
          }
          i(typeof c == "object" ? JSON.stringify(c, null, 2) : c.toString());
        } catch (C) {
          console.error("❌ Request failed:", C), i(`❌ Error: ${C.message}`);
        }
      },
      u = () => {
        n && (s.reset(), i(""));
      };
    return k.jsx(Id, {
      children: k.jsxs(Ln, {
        grow: !0,
        children: [
          k.jsxs(Ln.Col, {
            span: 4,
            className: "grid-column",
            children: [
              k.jsx(tt, {
                size: "xl",
                weight: 700,
                mt: 0,
                mb: 12,
                className: "tree-view-title",
                children: "Rescuebox CLI",
              }),
              k.jsx(W0, { tree: e, onCommandClick: l }),
            ],
          }),
          k.jsx(Ln.Col, {
            span: 8,
            className: "grid-column",
            children: n
              ? k.jsxs(k.Fragment, {
                  children: [
                    k.jsxs(pa, {
                      justify: "space-between",
                      mb: 8,
                      children: [
                        k.jsx(tt, {
                          size: "xl",
                          weight: 600,
                          children: n.name,
                        }),
                        k.jsx(Mr, {
                          variant: "light",
                          onClick: u,
                          children: "Reset",
                        }),
                      ],
                    }),
                    k.jsx(tt, {
                      mb: 12,
                      color: "dimmed",
                      children: n.help || "No description available.",
                    }),
                    k.jsx("form", {
                      onSubmit: a,
                      className: "command-form",
                      children: k.jsxs(ki, {
                        spacing: "xs",
                        mb: 12,
                        children: [
                          n.inputs.map((f) => {
                            var d;
                            return k.jsxs(
                              V,
                              {
                                children: [
                                  f.help &&
                                    k.jsx(tt, {
                                      size: "sm",
                                      color: "dimmed",
                                      mb: 4,
                                      children: f.help,
                                    }),
                                  f.type === "str" &&
                                    k.jsx(ye, {
                                      placeholder: f.default || "",
                                      ...s.getInputProps(f.name),
                                      required: !0,
                                    }),
                                  f.type === "int" &&
                                    k.jsx(ye, {
                                      type: "number",
                                      placeholder:
                                        ((d = f.default) == null
                                          ? void 0
                                          : d.toString()) || "",
                                      ...s.getInputProps(f.name),
                                      required: !0,
                                    }),
                                  f.type === "bool" &&
                                    k.jsx(bn, {
                                      label: f.name,
                                      ...s.getInputProps(f.name, {
                                        type: "checkbox",
                                      }),
                                    }),
                                ],
                              },
                              f.name
                            );
                          }),
                          k.jsx(Mr, {
                            type: "submit",
                            children: "Run Command",
                          }),
                        ],
                      }),
                    }),
                    k.jsx(tt, {
                      mt: 16,
                      mb: 4,
                      weight: 500,
                      children: "Command Output:",
                    }),
                    k.jsx(Ca, {
                      value: o,
                      readOnly: !0,
                      minRows: 10,
                      className: "command-output",
                    }),
                  ],
                })
              : k.jsx(tt, {
                  children:
                    "Select a command from the left panel to see details",
                }),
          }),
        ],
      }),
    });
  };
Cd(document.getElementById("react-root")).render(
  k.jsx(x.StrictMode, { children: k.jsx(U0, {}) })
);
