# Jekyll hook: nap skin brutalist + nut chuyen ngon ngu, KHONG sua layout cua Chirpy.
#
# Site gom 2 cay doc lap: /CTFWU (tieng Viet) va /CTFWU/en (tieng Anh), moi cay
# build tu _config rieng. Hook nay chen <link> CSS vao cuoi <head> va mot pill
# chuyen ngon ngu vau dau <body>, tinh URL cua cay kia tu chinh baseurl.

CTFW_BRUTALIST_CSS = "assets/css/brutalist.css".freeze

def ctfw_mirror_base(base)
  base == "/CTFWU" ? "/CTFWU/en" : "/CTFWU"
end

Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  next true unless doc.output_ext.to_s == ".html"
  base = doc.site.baseurl.to_s
  head = %(<link rel="stylesheet" href="#{base}/#{CTFW_BRUTALIST_CSS}">\n)
  head << %(<script>try{localStorage.setItem('theme','light')}catch(e){}</script>\n)
  doc.output = doc.output.sub("</head>", "#{head}</head>") if doc.output.include?("</head>")

  rest = doc.url.to_s.start_with?(base) ? doc.url.to_s[base.length..] : doc.url.to_s
  rest = "/" if rest.nil? || rest.empty?
  other = ctfw_mirror_base(base) + rest
  here_vi = !base.end_with?("/en")
  pill = %(<div class="ctfw-lang" id="ctfw-lang">) +
         %(<a href="#{base}#{rest}" aria-current="#{here_vi}">VI</a>) +
         %(<a href="#{other}" aria-current="#{!here_vi}">EN</a></div>\n)
  doc.output = doc.output.sub(%r{(<body[^>]*>)}) { Regexp.last_match(1) + "\n" + pill }
  true
end
