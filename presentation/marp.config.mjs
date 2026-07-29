// Marp CLI configuration for the NovaSteel deck.
//
// Marp Core renders emoji as remote <img> tags served from the Twemoji CDN by
// default, which makes the build depend on outbound network access and leaves
// broken glyphs in an offline PDF/PPTX. The deck uses emoji only as small
// semantic markers, so they are rendered as plain text with the system emoji
// font instead.

export default {
  options: {
    emoji: {
      shortcode: false,
      unicode: false,
    },
  },
};
