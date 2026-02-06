-- remove-comments.lua
-- Pandoc Lua filter: Removes all text enclosed in %% ... %%
-- and cleans up resulting empty structural blocks (lists, paragraphs).

local skipping = false

-- 1. Process text content
function Inlines(inlines)
  local result = pandoc.Inlines({})

  for _, el in ipairs(inlines) do
    if el.t == 'Str' then
      local text = el.text
      local output = ""
      local cursor = 1

      while cursor <= #text do
        if skipping then
          -- Currently inside a comment, looking for "%%"
          local s, e = text:find("%%%%", cursor)
          if s then
            skipping = false
            cursor = e + 1
          else
            cursor = #text + 1
          end
        else
          -- Currently visible, looking for "%%"
          local s, e = text:find("%%%%", cursor)
          if s then
            output = output .. text:sub(cursor, s - 1)
            skipping = true
            cursor = e + 1
          else
            output = output .. text:sub(cursor)
            cursor = #text + 1
          end
        end
      end

      if output ~= "" then
        result:insert(pandoc.Str(output))
      end

    elseif el.t == 'Space' or el.t == 'SoftBreak' or el.t == 'LineBreak' then
      if not skipping then result:insert(el) end
    else
      -- Other elements (Code, Strong, Emph, etc.)
      if not skipping then result:insert(el) end
    end
  end

  return result
end

-- 2. Cleanup Basic Blocks (Paragraphs, Headers)
function Para(el)
  if #el.content == 0 then return {} end
  return el
end

function Plain(el)
  if #el.content == 0 then return {} end
  return el
end

function Header(el)
  if #el.content == 0 then return {} end
  return el
end

-- 3. Cleanup List Containers
-- This removes list items that became empty, and removes the list if all items are gone.

local function cleanup_list(el)
  local new_items = pandoc.List()

  -- Iterate through list items (each item is a list of Blocks)
  for _, item in ipairs(el.content) do
    -- If the blocks inside the item were removed (by Para/Plain logic above),
    -- or if the item is empty, 'item' will have #item == 0.
    if #item > 0 then
      new_items:insert(item)
    end
  end

  -- If no items remain, remove the whole list object
  if #new_items == 0 then
    return {}
  end

  -- Otherwise, return the list with only the surviving items
  el.content = new_items
  return el
end

function BulletList(el) return cleanup_list(el) end
function OrderedList(el) return cleanup_list(el) end
function DefinitionList(el)
  -- Definition lists are slightly different structure, usually fine to leave or
  -- requires specific logic, but simple cleanup works if content is empty.
  if #el.content == 0 then return {} end
  return el
end