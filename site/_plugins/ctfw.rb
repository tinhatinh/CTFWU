# Jekyll hook: nap skin campus.css + nut chuyen ngon ngu, KHONG sua layout cua Chirpy.
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

# GitHub Pages dat Cache-Control: max-age=600 cho asset, nen sau khi doi skin
# van tro toi nguoi dung phai cho toi khi het 10 phut. Them moc thoi diem build
# vao URL de moi lan deploy la mot file moi.
CTFW_BUILD = Time.now.strftime("%Y%m%d%H%M")

Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  next true unless doc.output_ext.to_s == ".html"
  next true unless doc.output.include?("<body")

  base = doc.site.baseurl.to_s
  head = %(<link rel="stylesheet" href="#{base}/assets/css/campus.css?v=#{CTFW_BUILD}">) +
         %(<script defer src="#{base}/assets/js/lang.js?v=#{CTFW_BUILD}"></script>\n)

  rest = doc.url.to_s.start_with?(base) ? doc.url.to_s[base.length..-1].to_s : doc.url.to_s
  rest = "/" if rest.empty?
  here_vi = !base.end_with?("/en")
  # Nhan nao thi tro den ngon ngu do, khong phai "the o cay dang build" luon la VI:
  # o cay /en ma gan lien hien tai cho nut VI thi nut VI dung tai cho con nut EN
  # lai chay ve tieng Viet.
  vi_url = (here_vi ? base : ctfw_mirror_base(base)) + rest
  en_url = (here_vi ? ctfw_mirror_base(base) : base) + rest
  pill = %(<div class="ctfw-lang" id="ctfw-lang">) +
         %(<a href="#{vi_url}" aria-current="#{here_vi}">VI</a>) +
         %(<a href="#{en_url}" aria-current="#{!here_vi}">EN</a></div>\n)

  doc.output = doc.output.sub(%r{<body[^>]*>}) { |m| head + m + "\n" + pill }
  true
end
