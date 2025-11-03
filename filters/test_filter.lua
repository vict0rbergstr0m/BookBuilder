
-- simple_test_filter.lua
function Str(elem)
  return pandoc.Str(elem.text .. " [FILTERED]")
end

