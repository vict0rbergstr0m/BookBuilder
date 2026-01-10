-- remove-comments.lua
-- Pandoc Lua filter: Removes all text enclosed in %% ... %%

-- Global state to track if we are currently inside a comment
-- We use a global so the state persists across different paragraphs/blocks
local skipping = false

function Inlines(inlines)
  local result = pandoc.Inlines({})

  for _, el in ipairs(inlines) do
    if el.t == 'Str' then
      local text = el.text
      local output = ""
      local cursor = 1

      -- Loop through the string to handle cases like "Keep %%Delete%% Keep"
      while cursor <= #text do
        if skipping then
          -- We are currently hidden, looking for the closing "%%"
          -- Note: "%%%%" is the Lua pattern for a literal "%%"
          local s, e = text:find("%%%%", cursor)
          if s then
            -- Found the closing tag
            skipping = false
            cursor = e + 1
          else
            -- No closing tag in this string, discard the rest
            cursor = #text + 1
          end
        else
          -- We are visible, looking for the opening "%%"
          local s, e = text:find("%%%%", cursor)
          if s then
            -- Found an opening tag
            -- Keep the text before the "%%"
            output = output .. text:sub(cursor, s - 1)
            skipping = true
            cursor = e + 1
          else
            -- No opening tag, keep the rest of the string
            output = output .. text:sub(cursor)
            cursor = #text + 1
          end
        end
      end

      -- If we have any text left to show, add it to the result
      if output ~= "" then
        result:insert(pandoc.Str(output))
      end

    elseif el.t == 'Space' or el.t == 'SoftBreak' or el.t == 'LineBreak' then
      -- Handle whitespace: only keep it if we aren't skipping
      if not skipping then
        result:insert(el)
      end

    else
      -- Handle other elements (Bold, Italic, Code, etc.)
      -- If we are inside a comment, we remove the element entirely
      if not skipping then
        result:insert(el)
      end
    end
  end

  return result
end

-- Cleanup: Remove paragraphs that became empty after filtering
function Para(el)
  if #el.content == 0 then
    return {} -- Returning empty list removes the block
  end
  return el
end

-- Cleanup: Remove plain blocks that became empty
function Plain(el)
  if #el.content == 0 then
    return {}
  end
  return el
end