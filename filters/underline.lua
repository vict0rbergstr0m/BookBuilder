-- underline.lua
function RawInline (el)
  if el.format == "html" then
    -- For debugging, print what HTML raw inlines are being processed
    -- print("DEBUG RawInline HTML: " .. el.text)

    -- Match <u>text</u>, <u>text with spaces</u>, etc.
    -- Using (.-) for non-greedy match of content.
    local content = el.text:match("^<u>(.-)</u>$")
    if content then
      -- print("DEBUG Matched <u> content: " .. content)
      return pandoc.RawInline('latex', '\\underline{' .. content .. '}')
    end
  end
  return nil -- No change
end