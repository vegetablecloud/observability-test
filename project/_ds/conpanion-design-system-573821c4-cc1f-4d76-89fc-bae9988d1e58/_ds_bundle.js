/* @ds-bundle: {"format":4,"namespace":"ConpanionDesignSystem_573821","components":[{"name":"KeyMark","sourcePath":"components/brand/KeyMark.jsx"},{"name":"KeyPhoto","sourcePath":"components/brand/KeyPhoto.jsx"},{"name":"Logo","sourcePath":"components/brand/Logo.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"Eyebrow","sourcePath":"components/core/Eyebrow.jsx"},{"name":"Tag","sourcePath":"components/core/Tag.jsx"},{"name":"BulletList","sourcePath":"components/slides/BulletList.jsx"},{"name":"ContactBlock","sourcePath":"components/slides/ContactBlock.jsx"},{"name":"IconCard","sourcePath":"components/slides/IconCard.jsx"},{"name":"SlideFrame","sourcePath":"components/slides/SlideFrame.jsx"},{"name":"SlideTitle","sourcePath":"components/slides/SlideTitle.jsx"},{"name":"TechLogo","sourcePath":"components/slides/TechLogo.jsx"},{"name":"AgendaSlide","sourcePath":"slides/AgendaSlide.jsx"},{"name":"ClientsSlide","sourcePath":"slides/ClientsSlide.jsx"},{"name":"EndCardSlide","sourcePath":"slides/EndCardSlide.jsx"},{"name":"FullBleedSlide","sourcePath":"slides/FullBleedSlide.jsx"},{"name":"ImageLeftSlide","sourcePath":"slides/ImageLeftSlide.jsx"},{"name":"KeyNumbersSlide","sourcePath":"slides/KeyNumbersSlide.jsx"},{"name":"KeyPhotoSlide","sourcePath":"slides/KeyPhotoSlide.jsx"},{"name":"QuestionsSlide","sourcePath":"slides/QuestionsSlide.jsx"},{"name":"SectionSlide","sourcePath":"slides/SectionSlide.jsx"},{"name":"SixIconSlide","sourcePath":"slides/SixIconSlide.jsx"},{"name":"StatementSlide","sourcePath":"slides/StatementSlide.jsx"},{"name":"TeamSlide","sourcePath":"slides/TeamSlide.jsx"},{"name":"TechLogoSlide","sourcePath":"slides/TechLogoSlide.jsx"},{"name":"ThreeIconSlide","sourcePath":"slides/ThreeIconSlide.jsx"},{"name":"TimelineSlide","sourcePath":"slides/TimelineSlide.jsx"},{"name":"TitleContentSlide","sourcePath":"slides/TitleContentSlide.jsx"},{"name":"TitleSlide","sourcePath":"slides/TitleSlide.jsx"},{"name":"TwoContentSlide","sourcePath":"slides/TwoContentSlide.jsx"}],"sourceHashes":{"components/brand/KeyMark.jsx":"fc456e1e3f58","components/brand/KeyPhoto.jsx":"15118ee8d452","components/brand/Logo.jsx":"3a2e5efca122","components/core/Button.jsx":"c03be8918cc5","components/core/Card.jsx":"89835ea9b4fc","components/core/Eyebrow.jsx":"3a18d6810593","components/core/Tag.jsx":"76a06b33da03","components/slides/BulletList.jsx":"62bce7d6ae6a","components/slides/ContactBlock.jsx":"03bf220e368d","components/slides/IconCard.jsx":"bb9f004e7768","components/slides/SlideFrame.jsx":"f1c25bd56b03","components/slides/SlideTitle.jsx":"936b8ce7d943","components/slides/TechLogo.jsx":"b66000469ff4","slides/AgendaSlide.jsx":"8a73352ffb29","slides/ClientsSlide.jsx":"16a5681fa195","slides/EndCardSlide.jsx":"f06ad2924944","slides/FullBleedSlide.jsx":"f2f8a8140eaf","slides/ImageLeftSlide.jsx":"1cf49ab32ec2","slides/KeyNumbersSlide.jsx":"5d16d8a3d99b","slides/KeyPhotoSlide.jsx":"39d681c649ab","slides/QuestionsSlide.jsx":"f058f633d271","slides/SectionSlide.jsx":"c74e53152272","slides/SixIconSlide.jsx":"4d2b30060258","slides/StatementSlide.jsx":"ac0b63f28137","slides/TeamSlide.jsx":"b01891e1243e","slides/TechLogoSlide.jsx":"9d6c50f80e88","slides/ThreeIconSlide.jsx":"a7ae2ddff539","slides/TimelineSlide.jsx":"f6324e5789d2","slides/TitleContentSlide.jsx":"485c4d95a510","slides/TitleSlide.jsx":"63a1b4616412","slides/TwoContentSlide.jsx":"ca2a89274d57"},"inlinedExternals":[],"unexposedExports":[{"name":"keyPath","sourcePath":"components/brand/KeyMark.jsx"},{"name":"keyPoly","sourcePath":"components/brand/KeyMark.jsx"}]} */

(() => {

const __ds_ns = (window.ConpanionDesignSystem_573821 = window.ConpanionDesignSystem_573821 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/brand/KeyMark.jsx
try { (() => {
const FILLS = {
  yellow: 'var(--cp-yellow)',
  black: 'var(--cp-black)',
  white: 'var(--cp-white)'
};
const POLY = "106.59532 0 106.59532 164.29092 57.39513 164.29092 57.39513 49.28571 24.6001 49.28571 24.6001 0 106.59532 0";
const PATH = "M161.42274,242.33174c-1.8911-7.2696-4.73545-14.2004-8.45628-20.56135-2.69064-4.72836-5.88858-9.16408-9.45561-13.21476-2.27548-2.61832-4.68937-5.03641-7.30315-7.31585-4.04365-3.57323-8.47167-6.77682-13.19183-9.47214-6.34991-3.72721-13.26868-6.5765-20.52567-8.47098-6.5344-1.69416-13.42249-2.57207-20.49498-2.57207s-13.96058.87791-20.49498,2.57207c-7.25698,1.89448-14.17576,4.74378-20.52567,8.47098-4.72015,2.69531-9.14818,5.89891-13.19183,9.47214-2.61378,2.27943-5.02767,4.69753-7.30315,7.31585-3.56703,4.05068-6.76497,8.4864-9.45561,13.21476-3.72083,6.36095-6.56518,13.29175-8.45628,20.56135-1.69131,6.54576-2.5677,13.44573-2.5677,20.53061s.87639,13.98475,2.5677,20.53051c1.8911,7.26969,4.73545,14.2005,8.45628,20.56144,2.69064,4.72836,5.88858,9.16408,9.45561,13.21476,2.27548,2.61823,4.68937,5.03632,7.30315,7.31585,4.04365,3.57313,8.47167,6.77673,13.19183,9.47204,6.34991,3.72721,13.26868,6.57659,20.52567,8.47098,6.5344,1.69425,13.42249,2.57207,20.49498,2.57207s13.96058-.87782,20.49498-2.57207c7.25698-1.89439,14.17576-4.74378,20.52567-8.47098,4.72015-2.69531,9.14818-5.89891,13.19183-9.47204,2.61378-2.27953,5.02767-4.69762,7.30315-7.31585,3.56703-4.05068,6.76497-8.4864,9.45561-13.21476,3.72083-6.36095,6.56518-13.29175,8.45628-20.56144,1.69131-6.54576,2.5677-13.44573,2.5677-20.53051s-.87639-13.98485-2.5677-20.53061ZM113.76006,271.07143c-.75336,2.91096-1.8911,5.68326-3.38244,8.22459-1.07627,1.89439-2.35243,3.66563-3.7823,5.2828-.90717,1.04731-1.87571,2.01763-2.9213,2.92638-1.61436,1.43235-3.38244,2.71073-5.27363,3.78878-2.53683,1.49402-5.30441,2.63374-8.21023,3.38841-2.61378.67768-5.36588,1.03189-8.19493,1.03189s-5.58115-.35421-8.19493-1.03189c-2.90582-.75467-5.6734-1.89439-8.21023-3.38841-1.8912-1.07805-3.65927-2.35642-5.27363-3.78878-1.04559-.90875-2.01413-1.87907-2.9213-2.92638-1.42987-1.61717-2.70603-3.38841-3.7823-5.2828-1.49134-2.54133-2.62908-5.31363-3.38244-8.22459-.67651-2.61823-1.0302-5.37521-1.0302-8.20908s.35369-5.59086,1.0302-8.20918c.75336-2.91096,1.8911-5.68326,3.38244-8.22459,1.07627-1.89439,2.35243-3.66554,3.7823-5.2828.90717-1.04731,1.87571-2.01763,2.9213-2.92628,1.61436-1.43235,3.38244-2.71073,5.27363-3.78887,2.53683-1.49393,5.30441-2.63374,8.21023-3.38841,2.61378-.67768,5.36588-1.03189,8.19493-1.03189s5.58115.35421,8.19493,1.03189c2.90582.75467,5.6734,1.89448,8.21023,3.38841,1.8912,1.07814,3.65927,2.35652,5.27363,3.78887,1.04559.90865,2.01413,1.87897,2.9213,2.92628,1.42987,1.61726,2.70603,3.38841,3.7823,5.2828,1.49134,2.54133,2.62908,5.31363,3.38244,8.22459.67651,2.61832,1.0302,5.37521,1.0302,8.20918s-.35369,5.59086-1.0302,8.20908Z";
const keyPoly = POLY;
const keyPath = PATH;
function KeyMark({
  color = 'yellow',
  height = 101,
  style
}) {
  const fill = FILLS[color] || color;
  return /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 163.99045 345",
    height: height,
    width: height * 163.99045 / 345,
    style: style,
    role: "img",
    "aria-label": "Conpanion"
  }, /*#__PURE__*/React.createElement("polygon", {
    points: POLY,
    fill: fill
  }), /*#__PURE__*/React.createElement("path", {
    d: PATH,
    fill: fill
  }));
}
Object.assign(__ds_scope, { keyPoly, keyPath, KeyMark });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/KeyMark.jsx", error: String((e && e.message) || e) }); }

// components/brand/KeyPhoto.jsx
try { (() => {
/* Photograph clipped inside the key mark. Inline SVG clipPath so it renders everywhere.
   The mark is tall and narrow, so a landscape photo shows only a slim vertical slice — pick an
   image whose subject runs the full height, or pre-crop it. Default focus is the top of the
   frame; a centred crop of a horizon shot puts open water inside the "0" and the mark vanishes
   against black. assets/key-photo-city.png is a pre-rendered, correctly framed version. */
function KeyPhoto({
  src,
  height = 800,
  focus = "xMidYMin",
  style
}) {
  const id = React.useId().replace(/:/g, '');
  const w = height * 163.99045 / 345;
  return /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 163.99045 345",
    width: w,
    height: height,
    style: {
      display: 'block',
      ...style
    },
    role: "img",
    "aria-label": "Conpanion"
  }, /*#__PURE__*/React.createElement("defs", null, /*#__PURE__*/React.createElement("clipPath", {
    id: 'keyclip-' + id
  }, /*#__PURE__*/React.createElement("polygon", {
    points: __ds_scope.keyPoly
  }), /*#__PURE__*/React.createElement("path", {
    d: __ds_scope.keyPath
  }))), /*#__PURE__*/React.createElement("image", {
    href: src,
    x: "0",
    y: "0",
    width: "163.99045",
    height: "345",
    preserveAspectRatio: focus + " slice",
    clipPath: 'url(#keyclip-' + id + ')'
  }));
}
Object.assign(__ds_scope, { KeyPhoto });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/KeyPhoto.jsx", error: String((e && e.message) || e) }); }

// components/brand/Logo.jsx
try { (() => {
const SRC = {
  lockup: 'assets/logo-lockup.svg',
  wordmark: 'assets/wordmark-tagline.svg',
  onYellow: 'assets/wordmark-on-yellow.png'
};
function Logo({
  variant = 'lockup',
  width = 296,
  base = '',
  style
}) {
  return /*#__PURE__*/React.createElement("img", {
    src: base + SRC[variant],
    alt: "Conpanion",
    style: {
      width,
      display: 'block',
      ...style
    }
  });
}
Object.assign(__ds_scope, { Logo });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/Logo.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const SIZES = {
  sm: {
    padding: '8px 16px',
    fontSize: 11
  },
  md: {
    padding: '12px 24px',
    fontSize: 12
  },
  lg: {
    padding: '16px 32px',
    fontSize: 13
  }
};
const VARIANTS = {
  primary: {
    background: 'var(--cp-yellow)',
    color: 'var(--cp-black)',
    border: '1px solid var(--cp-yellow)'
  },
  secondary: {
    background: 'var(--cp-black)',
    color: 'var(--cp-white)',
    border: '1px solid var(--cp-black)'
  },
  ghost: {
    background: 'transparent',
    color: 'var(--cp-black)',
    border: '1px solid var(--cp-black)'
  }
};
function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  href,
  children,
  style,
  ...rest
}) {
  const Tag = href ? 'a' : 'button';
  const base = {
    ...(SIZES[size] || SIZES.md),
    ...(VARIANTS[variant] || VARIANTS.primary),
    fontFamily: 'var(--font-mono)',
    letterSpacing: 'var(--track-detail)',
    textTransform: 'uppercase',
    borderRadius: 'var(--radius-none)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.35 : 1,
    display: 'inline-block',
    textDecoration: 'none',
    lineHeight: 1.2,
    transition: 'background var(--dur-base) var(--ease-out), color var(--dur-base) var(--ease-out)',
    ...style
  };
  return /*#__PURE__*/React.createElement(Tag, _extends({
    href: href,
    disabled: !href && disabled ? true : undefined,
    style: base
  }, rest), children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function Card({
  accent = false,
  heading,
  eyebrow,
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--surface-card)',
      border: '1px solid var(--border-hairline)',
      borderTop: accent ? '3px solid var(--cp-yellow)' : '1px solid var(--border-hairline)',
      borderRadius: 'var(--radius-none)',
      padding: 24,
      fontFamily: 'var(--font-body)',
      ...style
    }
  }, eyebrow && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      letterSpacing: 'var(--track-detail)',
      textTransform: 'uppercase',
      color: 'var(--text-muted)',
      marginBottom: 10
    }
  }, eyebrow), heading && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      letterSpacing: 'var(--track-subhead)',
      fontSize: 20,
      lineHeight: 1,
      marginBottom: 10
    }
  }, heading), children && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      lineHeight: 'var(--lh-body)',
      color: 'var(--text-secondary)'
    }
  }, children));
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/Eyebrow.jsx
try { (() => {
function Eyebrow({
  rule = true,
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 12,
      letterSpacing: 'var(--track-detail)',
      textTransform: 'uppercase',
      color: 'var(--text-muted)',
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      ...style
    }
  }, rule && /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: 28,
      height: 2,
      background: 'var(--cp-yellow)',
      flex: 'none'
    }
  }), /*#__PURE__*/React.createElement("span", null, children));
}
Object.assign(__ds_scope, { Eyebrow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Eyebrow.jsx", error: String((e && e.message) || e) }); }

// components/core/Tag.jsx
try { (() => {
const TONES = {
  default: {
    background: 'transparent',
    color: 'var(--cp-black)',
    border: '1px solid var(--cp-grey-300)'
  },
  accent: {
    background: 'var(--cp-yellow)',
    color: 'var(--cp-black)',
    border: '1px solid var(--cp-yellow)'
  },
  dark: {
    background: 'var(--cp-black)',
    color: 'var(--cp-white)',
    border: '1px solid var(--cp-black)'
  }
};
function Tag({
  tone = 'default',
  children,
  style
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      ...(TONES[tone] || TONES.default),
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      letterSpacing: 'var(--track-detail)',
      textTransform: 'uppercase',
      padding: '5px 10px',
      lineHeight: 1.2,
      borderRadius: 'var(--radius-none)',
      display: 'inline-block',
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Tag.jsx", error: String((e && e.message) || e) }); }

// components/slides/BulletList.jsx
try { (() => {
const SIZES = ['var(--fs-body)', 'var(--fs-body-2)', 'var(--fs-body-3)', 'var(--fs-body-4)', 'var(--fs-body-4)'];
function BulletList({
  items = [],
  level = 1,
  style
}) {
  return /*#__PURE__*/React.createElement("ul", {
    style: {
      margin: 0,
      padding: 0,
      listStyle: 'none',
      fontSize: SIZES[level - 1],
      lineHeight: 'var(--lh-body)',
      ...style
    }
  }, items.map((t, i) => /*#__PURE__*/React.createElement("li", {
    key: i,
    style: {
      display: 'flex',
      gap: 12,
      marginTop: i ? 13 : 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      flex: 'none'
    }
  }, "\u2022"), /*#__PURE__*/React.createElement("span", null, t))));
}
Object.assign(__ds_scope, { BulletList });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/slides/BulletList.jsx", error: String((e && e.message) || e) }); }

// components/slides/ContactBlock.jsx
try { (() => {
function ContactBlock({
  lines = [],
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-heading)',
      fontSize: 'var(--fs-fine)',
      lineHeight: '20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 0,
      ...style
    }
  }, lines.map((l, i) => /*#__PURE__*/React.createElement("div", {
    key: i
  }, l)));
}
Object.assign(__ds_scope, { ContactBlock });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/slides/ContactBlock.jsx", error: String((e && e.message) || e) }); }

// components/slides/IconCard.jsx
try { (() => {
function IconCard({
  icon,
  iconAlt = '',
  heading,
  body,
  width = 374,
  base = '',
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width,
      fontFamily: 'var(--font-body)',
      ...style
    }
  }, icon && /*#__PURE__*/React.createElement("img", {
    src: base + 'assets/icons/' + icon + '.png',
    alt: iconAlt,
    style: {
      height: 66,
      display: 'block',
      marginBottom: 10
    }
  }), heading && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      fontSize: 'var(--fs-body-2)',
      lineHeight: 'var(--lh-tight)',
      marginBottom: 12
    }
  }, heading), body && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 'var(--fs-body-4)',
      lineHeight: 'var(--lh-body)'
    }
  }, body));
}
Object.assign(__ds_scope, { IconCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/slides/IconCard.jsx", error: String((e && e.message) || e) }); }

// components/slides/SlideFrame.jsx
try { (() => {
const GROUNDS = {
  paper: {
    bg: 'var(--surface-page)',
    ink: 'var(--cp-black)',
    mark: 'yellow'
  },
  yellow: {
    bg: 'var(--cp-yellow)',
    ink: 'var(--cp-black)',
    mark: 'black'
  },
  dark: {
    bg: 'var(--cp-black)',
    ink: 'var(--cp-white)',
    mark: 'yellow'
  }
};
function SlideFrame({
  ground = 'paper',
  footerBar = true,
  mark = true,
  children,
  style
}) {
  const g = GROUNDS[ground] || GROUNDS.paper;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      width: 1280,
      height: 720,
      overflow: 'hidden',
      background: g.bg,
      color: g.ink,
      fontFamily: 'var(--font-body)',
      fontSize: 'var(--fs-body)',
      ...style
    }
  }, children, footerBar && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 0,
      right: 0,
      bottom: 0,
      height: 38,
      background: 'var(--cp-yellow)'
    }
  }), mark && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 1178,
      top: 38
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.KeyMark, {
    color: g.mark,
    height: 101
  })));
}
Object.assign(__ds_scope, { SlideFrame });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/slides/SlideFrame.jsx", error: String((e && e.message) || e) }); }

// components/slides/SlideTitle.jsx
try { (() => {
function SlideTitle({
  children,
  x = 88,
  y = 38,
  width = 1104,
  size = 'var(--fs-title)',
  color,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: x,
      top: y,
      width,
      minHeight: 62,
      display: 'flex',
      alignItems: 'center',
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      fontSize: size,
      lineHeight: 'var(--lh-tight)',
      color: color || 'inherit',
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { SlideTitle });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/slides/SlideTitle.jsx", error: String((e && e.message) || e) }); }

// components/slides/TechLogo.jsx
try { (() => {
function TechLogo({
  name,
  height = 48,
  base = '',
  style
}) {
  return /*#__PURE__*/React.createElement("img", {
    src: base + 'assets/tech/' + name + '.png',
    alt: name.replace(/-/g, ' '),
    style: {
      height,
      width: 'auto',
      objectFit: 'contain',
      display: 'block',
      ...style
    }
  });
}
Object.assign(__ds_scope, { TechLogo });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/slides/TechLogo.jsx", error: String((e && e.message) || e) }); }

// slides/AgendaSlide.jsx
try { (() => {
const ROWS = [['01', 'Introduction', 'The name, our mission and our vision'], ['02', 'Why Conpanion', 'What you get when you choose us'], ['03', 'What we offer', 'Roles, tools and areas'], ['04', 'Our clients', 'A selection of who we work with']];
function AgendaSlide({
  title = 'Agenda',
  rows = ROWS
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, null, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 88,
      top: 170,
      width: 1104
    }
  }, rows.map(([n, h, s], i) => /*#__PURE__*/React.createElement("div", {
    key: n,
    style: {
      display: 'flex',
      gap: 32,
      alignItems: 'baseline',
      borderTop: '1px solid var(--cp-grey-300)',
      borderBottom: i === rows.length - 1 ? '1px solid var(--cp-grey-300)' : 'none',
      padding: '22px 0'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 64,
      fontFamily: 'var(--font-mono)',
      fontSize: 16,
      letterSpacing: 'var(--track-detail)',
      color: 'var(--text-muted)'
    }
  }, n), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 360,
      fontWeight: 'var(--fw-semibold)',
      fontSize: 26,
      letterSpacing: 'var(--track-subhead)'
    }
  }, h), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      fontSize: 20,
      lineHeight: 'var(--lh-body)',
      color: 'var(--text-secondary)'
    }
  }, s)))));
}
Object.assign(__ds_scope, { AgendaSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/AgendaSlide.jsx", error: String((e && e.message) || e) }); }

// slides/ClientsSlide.jsx
try { (() => {
function ClientsSlide({
  title = 'A selection of our clients',
  logos = []
}) {
  const cells = logos.length ? logos : Array.from({
    length: 10
  }, () => null);
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, null, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 88,
      top: 240,
      width: 1104,
      display: 'grid',
      gridTemplateColumns: 'repeat(5,1fr)',
      gap: 28
    }
  }, cells.map((src, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      height: 110,
      border: '1px solid var(--border-hairline)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'var(--font-mono)',
      fontSize: 10,
      letterSpacing: 'var(--track-detail)',
      color: 'var(--text-muted)'
    }
  }, src ? /*#__PURE__*/React.createElement("img", {
    src: src,
    alt: "",
    style: {
      maxHeight: 56,
      maxWidth: '80%',
      objectFit: 'contain'
    }
  }) : 'CLIENT LOGO'))));
}
Object.assign(__ds_scope, { ClientsSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/ClientsSlide.jsx", error: String((e && e.message) || e) }); }

// slides/EndCardSlide.jsx
try { (() => {
function EndCardSlide({
  base = ''
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "yellow",
    footerBar: false,
    mark: false
  }, /*#__PURE__*/React.createElement("img", {
    src: base + 'assets/endcard-yellow.png',
    alt: "Conpanion",
    style: {
      position: 'absolute',
      inset: 0,
      width: 1280,
      height: 720,
      objectFit: 'cover'
    }
  }));
}
Object.assign(__ds_scope, { EndCardSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/EndCardSlide.jsx", error: String((e && e.message) || e) }); }

// slides/FullBleedSlide.jsx
try { (() => {
function FullBleedSlide({
  image = 'assets/photo-city-harbour.jpg',
  caption = '',
  base = ''
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "dark",
    footerBar: false,
    mark: false
  }, /*#__PURE__*/React.createElement("img", {
    src: base + image,
    alt: "",
    style: {
      position: 'absolute',
      inset: 0,
      width: 1280,
      height: 720,
      objectFit: 'cover'
    }
  }), caption && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 0,
      bottom: 0,
      padding: '26px 88px',
      background: 'var(--cp-yellow)',
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      fontSize: 'var(--fs-body-2)',
      color: 'var(--cp-black)'
    }
  }, caption));
}
Object.assign(__ds_scope, { FullBleedSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/FullBleedSlide.jsx", error: String((e && e.message) || e) }); }

// slides/ImageLeftSlide.jsx
try { (() => {
function ImageLeftSlide({
  title = 'Close to you, wherever your data lives',
  image = 'assets/photo-city-harbour.jpg',
  items = ['Consultants on site and remote', 'Nordic delivery, Swedish contracts', 'Long engagements, low turnover'],
  base = ''
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "paper"
  }, /*#__PURE__*/React.createElement("img", {
    src: base + image,
    alt: "",
    style: {
      position: 'absolute',
      left: 0,
      top: 0,
      width: 490,
      height: 682,
      objectFit: 'cover'
    }
  }), /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, {
    x: 549,
    y: 61,
    width: 614
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 549,
      top: 154,
      width: 614
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.BulletList, {
    items: items,
    level: 2
  })));
}
Object.assign(__ds_scope, { ImageLeftSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/ImageLeftSlide.jsx", error: String((e && e.message) || e) }); }

// slides/KeyNumbersSlide.jsx
try { (() => {
/* Figures change often — always confirm them before a deck goes out. */
const STATS = [['18', 'Consultants', 'Data & Analytics specialists'], ['30', 'By 2028', 'Our growth target'], ['5', 'Competence areas', 'From engineering to AI/ML'], ['00', 'Metric', 'Replace with your figure']];
function KeyNumbersSlide({
  title = 'Conpanion in numbers',
  stats = STATS
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, null, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 88,
      top: 250,
      width: 1104,
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 40
    }
  }, stats.map(([n, h, s]) => /*#__PURE__*/React.createElement("div", {
    key: h
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 4,
      background: 'var(--cp-yellow)',
      marginBottom: 22
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      fontSize: 80,
      lineHeight: 'var(--lh-display)',
      letterSpacing: 'var(--track-headline)'
    }
  }, n), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      fontSize: 20,
      letterSpacing: 'var(--track-subhead)',
      marginTop: 18
    }
  }, h), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 17,
      lineHeight: 'var(--lh-body)',
      color: 'var(--text-secondary)',
      marginTop: 8
    }
  }, s)))));
}
Object.assign(__ds_scope, { KeyNumbersSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/KeyNumbersSlide.jsx", error: String((e && e.message) || e) }); }

// slides/KeyPhotoSlide.jsx
try { (() => {
/* Pre-rendered key-mark photo (assets/key-photo-city.png). For a different photograph,
   use the KeyPhoto component, which clips any image into the mark at runtime. */
function KeyPhotoSlide({
  image = 'assets/key-photo-city.png',
  height = 640,
  base = ''
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "dark",
    footerBar: false,
    mark: false
  }, /*#__PURE__*/React.createElement("img", {
    src: base + image,
    alt: "",
    style: {
      position: 'absolute',
      left: '50%',
      top: '50%',
      transform: 'translate(-50%,-50%)',
      height,
      width: height * 163.99045 / 345
    }
  }));
}
Object.assign(__ds_scope, { KeyPhotoSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/KeyPhotoSlide.jsx", error: String((e && e.message) || e) }); }

// slides/QuestionsSlide.jsx
try { (() => {
function QuestionsSlide({
  title = 'Questions?'
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "yellow",
    footerBar: false
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 195,
      top: 314,
      width: 890,
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      letterSpacing: 'var(--track-headline)',
      fontSize: 'var(--fs-section)',
      lineHeight: 'var(--lh-heading)'
    }
  }, title));
}
Object.assign(__ds_scope, { QuestionsSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/QuestionsSlide.jsx", error: String((e && e.message) || e) }); }

// slides/SectionSlide.jsx
try { (() => {
function SectionSlide({
  title = 'Where we start',
  subtitle = 'A short line that frames the section'
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "yellow",
    footerBar: false
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 195,
      top: 324,
      width: 890,
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      letterSpacing: 'var(--track-headline)',
      fontSize: 'var(--fs-section)',
      lineHeight: 'var(--lh-tight)'
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 195,
      top: 404,
      width: 890,
      fontFamily: 'var(--font-heading)',
      fontSize: 'var(--fs-body-2)'
    }
  }, subtitle));
}
Object.assign(__ds_scope, { SectionSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/SectionSlide.jsx", error: String((e && e.message) || e) }); }

// slides/SixIconSlide.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const DEF = [{
  icon: 'database',
  heading: 'Data platform',
  body: 'Lakehouse and warehouse on Azure.'
}, {
  icon: 'exchange-arrows',
  heading: 'Integration',
  body: 'Reliable pipelines between your systems.'
}, {
  icon: 'table-grid',
  heading: 'Modelling',
  body: 'Governed, tested, documented models.'
}, {
  icon: 'chart-up',
  heading: 'Analytics',
  body: 'Power BI, Qlik and Tableau reporting.'
}, {
  icon: 'gdpr',
  heading: 'Governance',
  body: 'Access, lineage and GDPR in place.'
}, {
  icon: 'people-group',
  heading: 'Enablement',
  body: 'Your team, trained and self-sufficient.'
}];
function SixIconSlide({
  title = 'What we do',
  cards = DEF,
  base = ''
}) {
  const X = [50, 452, 853],
    Y = [170, 395];
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "paper"
  }, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), cards.slice(0, 6).map((c, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      position: 'absolute',
      left: X[i % 3],
      top: Y[Math.floor(i / 3)],
      width: 374
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.IconCard, _extends({}, c, {
    base: base,
    width: 374
  })))));
}
Object.assign(__ds_scope, { SixIconSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/SixIconSlide.jsx", error: String((e && e.message) || e) }); }

// slides/StatementSlide.jsx
try { (() => {
function StatementSlide({
  statement = 'We unlock the power of data',
  attribution = '',
  base = ''
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "dark",
    footerBar: false
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 195,
      top: 300,
      width: 890,
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      letterSpacing: 'var(--track-headline)',
      fontSize: 'var(--fs-section)',
      lineHeight: 'var(--lh-tight)',
      color: 'var(--cp-white)'
    }
  }, statement), attribution && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 195,
      top: 420,
      width: 890,
      fontFamily: 'var(--font-heading)',
      fontSize: 'var(--fs-body-2)',
      color: 'var(--cp-yellow)'
    }
  }, attribution));
}
Object.assign(__ds_scope, { StatementSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/StatementSlide.jsx", error: String((e && e.message) || e) }); }

// slides/TeamSlide.jsx
try { (() => {
const PEOPLE = [{}, {}, {}, {}];
function TeamSlide({
  title = 'The team on this engagement',
  people = PEOPLE
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, null, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 88,
      top: 180,
      width: 1104,
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 32
    }
  }, people.map((p, i) => /*#__PURE__*/React.createElement("div", {
    key: i
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 240,
      background: 'var(--surface-sunken)',
      border: '1px solid var(--border-hairline)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'var(--font-mono)',
      fontSize: 11,
      letterSpacing: 'var(--track-detail)',
      color: 'var(--text-muted)',
      backgroundImage: p.photo ? 'url(' + p.photo + ')' : 'none',
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }, p.photo ? '' : 'PHOTO'), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      fontSize: 20,
      letterSpacing: 'var(--track-subhead)',
      marginTop: 16
    }
  }, p.name || 'Presenter name'), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      color: 'var(--text-secondary)',
      marginTop: 6
    }
  }, p.role || 'Role')))));
}
Object.assign(__ds_scope, { TeamSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/TeamSlide.jsx", error: String((e && e.message) || e) }); }

// slides/TechLogoSlide.jsx
try { (() => {
const DEF = ['azure', 'databricks', 'microsoft-fabric', 'snowflake', 'google-bigquery', 'power-bi', 'qlik', 'tableau', 'looker', 'dbt', 'python', 'apache-spark'];
function TechLogoSlide({
  title = 'The stack we work in',
  logos = DEF,
  base = ''
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "paper"
  }, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 88,
      top: 190,
      width: 1104,
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: '56px 40px',
      alignItems: 'center',
      justifyItems: 'center'
    }
  }, logos.map(n => /*#__PURE__*/React.createElement(__ds_scope.TechLogo, {
    key: n,
    name: n,
    height: 54,
    base: base
  }))));
}
Object.assign(__ds_scope, { TechLogoSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/TechLogoSlide.jsx", error: String((e && e.message) || e) }); }

// slides/ThreeIconSlide.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const DEF = [{
  icon: 'compass',
  heading: 'Direction',
  body: 'We agree the decisions the data has to support before we touch a pipeline.'
}, {
  icon: 'pipeline-flow',
  heading: 'Platform',
  body: 'Ingestion, storage and modelling on Azure, Databricks or Fabric.'
}, {
  icon: 'chart-up',
  heading: 'Adoption',
  body: 'Reporting people use, and a team that knows how it works.'
}];
function ThreeIconSlide({
  title = 'How we work',
  cards = DEF,
  base = ''
}) {
  const X = [52, 454, 855];
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "paper"
  }, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), cards.slice(0, 3).map((c, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      position: 'absolute',
      left: X[i],
      top: 243,
      width: 374
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.IconCard, _extends({}, c, {
    base: base,
    width: 374
  })))));
}
Object.assign(__ds_scope, { ThreeIconSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/ThreeIconSlide.jsx", error: String((e && e.message) || e) }); }

// slides/TimelineSlide.jsx
try { (() => {
const STEPS = [['2021', 'Founded', 'Started in Jönköping'], ['2022', 'Second office', 'Opened in Skövde'], ['2025', 'Third location', '18 consultants'], ['2028', 'Where we are going', '30 employees']];
function TimelineSlide({
  title = 'Our story so far',
  steps = STEPS
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, null, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 88,
      top: 331,
      width: 1104,
      height: 2,
      background: 'var(--cp-grey-300)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 88,
      top: 280,
      width: 1104,
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 32
    }
  }, steps.map(([y, h, s], i) => /*#__PURE__*/React.createElement("div", {
    key: y,
    style: {
      display: 'flex',
      flexDirection: 'column'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 16,
      letterSpacing: 'var(--track-detail)',
      color: 'var(--text-muted)'
    }
  }, y), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 22
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 18,
      height: 18,
      background: i === steps.length - 1 ? 'var(--cp-black)' : 'var(--cp-yellow)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      height: 28
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      fontSize: 22,
      letterSpacing: 'var(--track-subhead)'
    }
  }, h), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 17,
      lineHeight: 'var(--lh-body)',
      color: 'var(--text-secondary)',
      marginTop: 8
    }
  }, s)))));
}
Object.assign(__ds_scope, { TimelineSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/TimelineSlide.jsx", error: String((e && e.message) || e) }); }

// slides/TitleContentSlide.jsx
try { (() => {
function TitleContentSlide({
  title = 'Our delivery model',
  items = ['One team from platform to report', 'Governed models, documented and tested', 'Handover that leaves your people in control', 'Fixed cadence, visible backlog']
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "paper"
  }, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 88,
      top: 155,
      width: 1104
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.BulletList, {
    items: items
  })));
}
Object.assign(__ds_scope, { TitleContentSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/TitleContentSlide.jsx", error: String((e && e.message) || e) }); }

// slides/TitleSlide.jsx
try { (() => {
function TitleSlide({
  name = 'Presenter name',
  role = 'Role',
  headline = 'We unlock the power of data',
  contact = ['+46 70 000 00 00', 'name@conpanion.se', 'conpanion.se'],
  photo = 'assets/photo-city-aerial.jpg',
  base = ''
}) {
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "dark",
    footerBar: false
  }, /*#__PURE__*/React.createElement("img", {
    src: base + photo,
    alt: "",
    style: {
      position: 'absolute',
      inset: 0,
      width: 1280,
      height: 720,
      objectFit: 'cover'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      background: '#000000',
      opacity: 0.45
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 0,
      top: 318,
      width: 773,
      height: 301,
      background: 'var(--cp-yellow)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 18,
      top: 338,
      width: 848,
      fontFamily: 'var(--font-heading)',
      fontSize: 'var(--fs-body-2)',
      color: 'var(--cp-black)'
    }
  }, headline), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 18,
      top: 414,
      width: 552,
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      letterSpacing: 'var(--track-headline)',
      fontSize: 'var(--fs-cover-name)',
      lineHeight: 'var(--lh-tight)',
      color: 'var(--cp-black)'
    }
  }, name), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 18,
      top: 462,
      width: 552,
      fontFamily: 'var(--font-heading)',
      fontStyle: 'italic',
      fontSize: 'var(--fs-body-2)',
      color: 'var(--cp-black)'
    }
  }, role), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: 18,
      top: 540
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Logo, {
    variant: "wordmark",
    width: 296,
    base: base
  })), /*#__PURE__*/React.createElement(__ds_scope.ContactBlock, {
    lines: contact,
    style: {
      position: 'absolute',
      left: 554,
      top: 533,
      width: 207,
      color: 'var(--cp-black)'
    }
  }));
}
Object.assign(__ds_scope, { TitleSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/TitleSlide.jsx", error: String((e && e.message) || e) }); }

// slides/TwoContentSlide.jsx
try { (() => {
function TwoContentSlide({
  title = 'Today and after',
  leftHeading = 'Today',
  left = ['Reports built by hand', 'Numbers argued in meetings', 'Key logic in one person\'s head'],
  rightHeading = 'After',
  right = ['One governed model', 'One version of each number', 'Documented, tested, owned']
}) {
  const col = (h, items, x) => /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: x,
      top: 155,
      width: 544
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-heading)',
      fontWeight: 'var(--fw-semibold)',
      fontSize: 'var(--fs-body-2)',
      marginBottom: 18
    }
  }, h), /*#__PURE__*/React.createElement(__ds_scope.BulletList, {
    items: items,
    level: 2
  }));
  return /*#__PURE__*/React.createElement(__ds_scope.SlideFrame, {
    ground: "paper"
  }, /*#__PURE__*/React.createElement(__ds_scope.SlideTitle, null, title), col(leftHeading, left, 88), col(rightHeading, right, 648));
}
Object.assign(__ds_scope, { TwoContentSlide });
})(); } catch (e) { __ds_ns.__errors.push({ path: "slides/TwoContentSlide.jsx", error: String((e && e.message) || e) }); }

__ds_ns.KeyMark = __ds_scope.KeyMark;

__ds_ns.KeyPhoto = __ds_scope.KeyPhoto;

__ds_ns.Logo = __ds_scope.Logo;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Eyebrow = __ds_scope.Eyebrow;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.BulletList = __ds_scope.BulletList;

__ds_ns.ContactBlock = __ds_scope.ContactBlock;

__ds_ns.IconCard = __ds_scope.IconCard;

__ds_ns.SlideFrame = __ds_scope.SlideFrame;

__ds_ns.SlideTitle = __ds_scope.SlideTitle;

__ds_ns.TechLogo = __ds_scope.TechLogo;

__ds_ns.AgendaSlide = __ds_scope.AgendaSlide;

__ds_ns.ClientsSlide = __ds_scope.ClientsSlide;

__ds_ns.EndCardSlide = __ds_scope.EndCardSlide;

__ds_ns.FullBleedSlide = __ds_scope.FullBleedSlide;

__ds_ns.ImageLeftSlide = __ds_scope.ImageLeftSlide;

__ds_ns.KeyNumbersSlide = __ds_scope.KeyNumbersSlide;

__ds_ns.KeyPhotoSlide = __ds_scope.KeyPhotoSlide;

__ds_ns.QuestionsSlide = __ds_scope.QuestionsSlide;

__ds_ns.SectionSlide = __ds_scope.SectionSlide;

__ds_ns.SixIconSlide = __ds_scope.SixIconSlide;

__ds_ns.StatementSlide = __ds_scope.StatementSlide;

__ds_ns.TeamSlide = __ds_scope.TeamSlide;

__ds_ns.TechLogoSlide = __ds_scope.TechLogoSlide;

__ds_ns.ThreeIconSlide = __ds_scope.ThreeIconSlide;

__ds_ns.TimelineSlide = __ds_scope.TimelineSlide;

__ds_ns.TitleContentSlide = __ds_scope.TitleContentSlide;

__ds_ns.TitleSlide = __ds_scope.TitleSlide;

__ds_ns.TwoContentSlide = __ds_scope.TwoContentSlide;

})();
