# Jekyll hook: nap skin brutalist + nut chuyen ngon ngu, KHONG sua layout cua Chirpy.
#
# Site gom 2 cay doc lap: /CTFWU (tieng Viet) va /CTFWU/en (tieng Anh), moi cay
# build tu _config rieng.
#
# Neo vao the <body>, khong neo vao </head>: Chirpy bat compress_html voi
# `endings: all` nen the dong </head> bi loai trong HTML dau ra (sub("</head>")
# chua bao gio khop). Chen ngay truoc <body> van nam trong head.

def ctfw_mirror_base(base)
  base == "/CTFWU" ? "/CTFWU/en" : "/CTFWU"
end

Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  next true unless doc.output_ext.to_s == ".html"
  next true unless doc.output.include?("<body")

  base = doc.site.baseurl.to_s
  head = %(<link rel="stylesheet" href="#{base}/assets/css/brutalist.css">\n)
  head << %(<script>try{localStorage.setItem('theme','light')}catch(e){}</script>\n)

  rest = doc.url.to_s.start_with?(base) ? doc.url.to_s[base.length..-1].to_s : doc.url.to_s
  rest = "/" if rest.empty?
  other = ctfw_mirror_base(base) + rest
  here_vi = !base.end_with?("/en")
  pill = %(<div class="ctfw-lang" id="ctfw-lang">) +
         %(<a href="#{base}#{rest}" aria-current="#{here_vi}">VI</a>) +
         %(<a href="#{other}" aria-current="#{!here_vi}">EN</a></div>\n)

  doc.output = doc.output.sub(%r{<body[^>]*>}) { |m| head + m + "\n" + pill }
  true
end
