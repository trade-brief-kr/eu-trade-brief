# 유럽 통상 브리프 — 조사·작성 기준 (Codex 일일 조사 프롬프트에 그대로 포함됨)

## 독자·목적
- 독자: 유럽과 거래·협력하는 한국 기업인, 공관·기관 관계자 등 일반 한국 독자.
- 목적: 최근 24시간 EU 차원 주요 통상·경제 이슈와 유럽 각국 주요 뉴스를 한눈에 파악.
- 내부 업무용 표현(확인 필요, 오늘 확인할 것, 검토 바람, 담당 등) 사용 금지. 사실 전달형 문장만.

## 구성
0. 한 줄 요약 (lead, 선택)
   - 오늘 보고서에 수록한 사실만으로 EU Top Issues와 핵심 국가 이슈를 한 문장으로 요약.
   - 한국어, 명사형 종결, 대략 80–140자. 내부 업무 표현·추측 금지. 적절한 요약이 없으면 필드 생략.
1. ★ EU Top Issues (topIssues, 5건 목표, 최소 3건)
   - EU 차원 이슈: 집행위원회·이사회·유럽의회·유럽이사회 결정, 통상정책(FTA, 무역구제·반덤핑·세이프가드, 대미·대중 통상),
     CBAM·배터리규정·핵심원자재법·AI법 등 규제, 대러 제재, 산업·보조금 정책, ECB 통화정책, Eurostat 주요 통계 발표.
   - 한 건 = 한 문장(필요 시 두 문장) 요약 + 원 출처 1개. 문장은 명사형 종결(~발표, ~합의, ~전망).
   - 한국 기업에 직접 영향이 있는 사안(한국산 제품 무역구제, 한-EU 협력, 한국 기업 투자 등)을 우선 반영.
2. ★ 일일보도동향 (countryNews) — 국가별 주요 뉴스 1~2건
   - 국가별로 그 나라 현지어 주요 매체·정부·통계청·중앙은행 발표에서 가장 중요한 뉴스 1~2건만.
   - 각 건: 제목(짧은 한 줄) + bullet 1~2개(각 80자 안팎, 명사형 종결) + 원 출처.
   - 뉴스가 없거나 확인 안 되는 국가는 생략(빈 항목·채우기용 일반론 금지). 주요국(독일·프랑스·영국·이탈리아·스페인·
     네덜란드·폴란드·벨기에·스웨덴·스위스·오스트리아·체코·헝가리·슬로바키아·루마니아 등)은 최대한 포함.
   - EU Top Issues와 같은 사안을 국가란에 반복하지 말 것(그 나라 고유의 후속·국내 반응이면 가능).

## 출처 원칙
- 반드시 실제 웹 검색으로 찾고 원문 페이지를 열어 날짜·내용을 확인한 것만. 추측·기억·날조 URL 금지.
- 각국 현지어 주요 매체 우선(예: 독일 Handelsblatt·FAZ·Süddeutsche·Spiegel·tagesschau, 프랑스 Les Echos·Le Monde·Le Figaro,
  영국 FT·BBC·Guardian·Reuters UK, 이탈리아 Il Sole 24 Ore·Corriere della Sera·ANSA, 스페인 El País·Expansión·Cinco Días,
  네덜란드 NOS·FD·NRC, 폴란드 Rzeczpospolita·Business Insider Polska·PAP, 체코 Hospodářské noviny·ČTK·iROZHLAS,
  헝가리 Portfolio·HVG·Telex·MTI, 슬로바키아 SME·Denník N·TASR, 루마니아 Ziarul Financiar·Agerpres, 오스트리아 Der Standard·
  Die Presse·ORF, 스웨덴 Dagens Industri·SVT, 스위스 NZZ·SRF, 벨기에 De Tijd·L'Echo, 덴마크 Børsen·DR, 핀란드 Yle·HS,
  노르웨이 NRK·E24, 포르투갈 Público·Expresso, 그리스 Kathimerini, 불가리아 BTA, 크로아티아 HINA, 세르비아 RTS·Tanjug 등),
  각국 정부·통계청·중앙은행 공식 발표. EU 이슈는 European Commission·Council·Parliament·ECB·Eurostat 원문 우선.
- 원 매체 URL을 url에 기재. 원 기사가 유료이거나 다른 매체가 같은 내용을 재게재한 경우 그 재게재 URL은 altUrl.
- 매체명(source)은 원 매체 이름 그대로(예: "Handelsblatt", "European Commission").
- 게재일시(publishedAt, ISO 8601, 시간대 포함)를 원문에서 확인해 기재. 기준 시각 기준 24시간 이내만.
  전날 브리프에서 빠진 중요 사안을 보완할 때만 72시간 이내 허용, text 앞에 "[누락 보완]" 표기.

## 작성 원칙
- 한국어, 명사형 종결, 간결. 현지어 고유명사는 한국어 표기 후 필요 시 괄호에 원어.
- 단계 구분(제안/합의/채택/발효/시행/전망)과 수치·날짜는 원문 그대로.
- 같은 사안은 하나로 통합, 출처는 가장 권위 있는 1~2개.
- 한국 관련 항목은 korea: true.
