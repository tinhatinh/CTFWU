# Markdown assets are shared by the independent Vietnamese and English builds.
Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  next unless doc.output_ext == '.html'
  base = doc.site.baseurl.to_s
  doc.output = doc.output.gsub(%r{(src|href)="/assets/}, "\\1=\"#{base}/assets/")
end
