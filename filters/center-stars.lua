-- center-stars.lua
-- Pandoc Lua filter: Center paragraphs containing only "*" and replace with a custom marker in LaTeX

-- Replace this with whatever you want to show in the PDF
local replacement = "***"  -- Example: "◇", "❧", "***"

function Para(el)
  -- Check if paragraph contains exactly one string and it is "*"
  if #el.content == 1 then
    local c = el.content[1]
    if c.t == "Str" and c.text == "*" then
      -- Replace with centered LaTeX block
      return pandoc.RawBlock("latex", "\\begin{center}" .. replacement .. "\\end{center}")
    end
  end

  return el
end
