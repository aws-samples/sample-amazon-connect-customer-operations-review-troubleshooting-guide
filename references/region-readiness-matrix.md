# Amazon Connect Region Readiness Matrix

> **Generated file — do not edit by hand.** Regenerate with `python3 scripts/build_region_data.py`.
> Snapshot built 2026-10-06. Telecoms Coverage Guide "Last updated": 1st October 2026.
> This is a point-in-time copy of the AWS sources listed at the end. AWS changes them without notice —
> re-check the live pages before committing to a Region.

Legend: ✅ available · ❌ not listed for that Region · `Yes*` = as printed on the AWS page (no footnote published).

## 1. Amazon Connect home Regions

| Region | Code | FIPS endpoint | Global Resiliency partner |
|---|---|---|---|
| Africa (Cape Town) | `af-south-1` | — | — |
| Asia Pacific (Tokyo) | `ap-northeast-1` | — | `ap-northeast-3` |
| Asia Pacific (Seoul) | `ap-northeast-2` | — | — |
| Asia Pacific (Singapore) | `ap-southeast-1` | — | — |
| Asia Pacific (Sydney) | `ap-southeast-2` | — | — |
| Canada (Central) | `ca-central-1` | ✅ | — |
| Europe (Frankfurt) | `eu-central-1` | — | `eu-west-2` |
| Europe (London) | `eu-west-2` | — | `eu-central-1` |
| US East (N. Virginia) | `us-east-1` | ✅ | `us-west-2` |
| AWS GovCloud (US-West) | `us-gov-west-1` | — | — |
| US West (Oregon) | `us-west-2` | ✅ | `us-east-1` |

`ap-northeast-3` (Osaka) is a Global Resiliency **replica-only** Region — not a home Region.

## 2. Feature availability by Region

| Feature (key) | `af-south-1` | `ap-northeast-1` | `ap-northeast-2` | `ap-southeast-1` | `ap-southeast-2` | `ca-central-1` | `eu-central-1` | `eu-west-2` | `us-east-1` | `us-gov-west-1` | `us-west-2` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Agent assist (Amazon Q in Connect / AI agents) (`agent_assist`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Agent workspace and step-by-step guides (`agent_workspace`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agent workspace third-party applications (`agent_workspace_3p_apps`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Agentic CX Designer (`agentic_cx_designer`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Amazon Connect agentic voice (`agentic_voice`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| AppIntegrations (`app_integrations`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Cases (`cases`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Communications widget (`communications_widget`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Conversational analytics (Contact Lens) (`conversational_analytics`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Customer authentication (`customer_authentication`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Customer Profiles (`customer_profiles`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Customer Profiles calculated attributes API (`customer_profiles_calculated_attributes`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Analytics data lake (`data_lake`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| External Tool (`external_tool`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Forecasting & agent scheduling (`forecasting_scheduling`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Global Resiliency (ACGR) (`global_resiliency`) | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| In-app, web, and video calling (`inapp_web_video_calling`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Live media streaming (`live_media_streaming`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Messaging integrations (`messaging`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Outbound campaigns (`outbound_campaigns`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Tasks (`tasks`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Voice ID (`voice_id`) | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |

### Messaging integrations — sub-features

| Sub-feature (key) | `af-south-1` | `ap-northeast-1` | `ap-northeast-2` | `ap-southeast-1` | `ap-southeast-2` | `ca-central-1` | `eu-central-1` | `eu-west-2` | `us-east-1` | `us-gov-west-1` | `us-west-2` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Apple Messages for Business (`messaging.apple_messages_for_business`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Push notifications (`messaging.push_notifications`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| SMS (`messaging.sms`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| WhatsApp Business Messaging (`messaging.whatsapp_business_messaging`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |

### Conversational analytics (Contact Lens) — sub-features

| Sub-feature (key) | `af-south-1` | `ap-northeast-1` | `ap-northeast-2` | `ap-southeast-1` | `ap-southeast-2` | `ca-central-1` | `eu-central-1` | `eu-west-2` | `us-east-1` | `us-gov-west-1` | `us-west-2` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Analytics dashboards (`conversational_analytics.analytics_dashboards`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| External voice (`conversational_analytics.external_voice`) | Recording | Recording, Streaming | Recording | Recording | Recording, Streaming | Recording, Streaming | Recording, Streaming | Recording, Streaming | Recording, Streaming | ❌ | Recording, Streaming |
| Generative AI-powered contact categorization (`conversational_analytics.generative_ai_powered_contact_categorization`) | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Generative AI-powered information extraction (`conversational_analytics.generative_ai_powered_information_extraction`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Generative AI-powered performance evaluations (`conversational_analytics.generative_ai_powered_performance_evaluations`) | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Generative AI-powered post-contact summaries (`conversational_analytics.generative_ai_powered_post_contact_summaries`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Performance evaluations (`conversational_analytics.performance_evaluations`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Post-call analytics (`conversational_analytics.post_call_analytics`) | ✅ | ✅ | ✅ | ✅ | ✅ | Yes* | ✅ | Yes* | ✅ | ✅ | ✅ |
| Post-chat analytics (`conversational_analytics.post_chat_analytics`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Real-time call analytics (`conversational_analytics.real_time_call_analytics`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Screen recording (`conversational_analytics.screen_recording`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Theme detection (`conversational_analytics.theme_detection`) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |

## 3. Outbound campaigns — callable destinations by home Region

> **Where the two columns differ for a home Region (marked ⚠️ `REG-011`), the AWS sources disagree: report both destination lists and flag `REG-011` — do not pick one. Tell the customer to confirm with AWS before committing. `REG-011` is in addition to, never instead of, the finding for the destination itself — an unsupported destination (e.g. Europe (London) → US) is always `REG-007`.**

| Home Region | Destination countries (regions page) | Destination countries (Telecoms guide `Outbound Campaign Regions` column) |
|---|---|---|
| `af-south-1` | ZA | ZA |
| `ap-northeast-1` | JP | JP |
| `ap-northeast-2` | KR | KR |
| `ap-southeast-1` ⚠️ `REG-011` | MY, PH, SG, TH, VN | MY, PH, SG, TH |
| `ap-southeast-2` | AU, NZ | AU, NZ |
| `ca-central-1` | CA | CA |
| `eu-central-1` | BE, DE, DK, ES, FR, GB, IE, IT, NL, PL, PT | BE, DE, DK, ES, FR, GB, IE, IT, NL, PL, PT |
| `eu-west-2` | BE, DE, DK, ES, FR, GB, IE, IT, NL, PL, PT | BE, DE, DK, ES, FR, GB, IE, IT, NL, PL, PT |
| `us-east-1` ⚠️ `REG-011` | BR, MX, US | BR, MX, PR, US |
| `us-gov-west-1` | — | — |
| `us-west-2` ⚠️ `REG-011` | BR, MX, US | BR, MX, PR, US |

- From instances created in Asia Pacific (Sydney) you can call phone numbers based in Australia and New Zealand. There are a few specific restrictions explained in Make predictive and progressive calls using Connect Customer outbound campaigns ).
- No other combinations are supported. For example, you can't make campaign calls from Europe (London) to US phone numbers, or from Europe (Frankfurt) to New Zealand phone numbers (`REG-007`).

## 4. Countries callable by default (outbound allow-list)

| Home Region | Default countries |
|---|---|
| `af-south-1` | ZA, GB, US |
| `ap-northeast-1` | JP, VN, US |
| `ap-northeast-2` | KR, GB, US |
| `ap-southeast-1` | SG, AU, HK, US, GB |
| `ap-southeast-2` | AU, NZ, US |
| `ca-central-1` | US, CA, MX, PR, GB |
| `eu-central-1` | GB, IT, FR, IE, US |
| `eu-west-2` | GB, IT, FR, IE, US |
| `us-east-1` | US, CA, MX, PR, GB |
| `us-gov-west-1` | US, CA, MX, PR, GB |
| `us-west-2` | US, CA, MX, PR, GB |

- UK mobile numbers with the following prefix might not be allowed by default: +447
- Japan mobile numbers with the following prefixes might not be allowed by default: +8170, 8180, and 8190

## 5. Phone numbers by country (Telecoms Coverage Guide)

Ticks: ✅ supported · 🟡 conditional (yellow tick in the PDF) · ❌ not supported. Region: where the number can be claimed/managed.

| Country | Type | Avail | Nat OB | Intl OB | Port | Multi-carrier | Custom CLI | Claimable in | Campaign Regions | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Albania (AL) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Albania (AL) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Armenia (AM) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Algeria (DZ) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Angola (AO) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Anguilla (AI) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Antigua and Barbuda (AG) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Argentina (AR) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Argentina (AR) | Shared Cost | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Argentina (AR) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Argentina (AR) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Australia (AU) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | ap-southeast-2 | GA |
| Australia (AU) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Australia (AU) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Austria (AT) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | — | GA |
| Austria (AT) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | — | GA |
| Austria (AT) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Azerbaijan (AZ) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Bahrain (BH) | DID | ✅(1) | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Bahamas (BS) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Bangladesh (BD) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Barbados (BB) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Belarus (BY) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Belgium (BE) | DID (mobile) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Belgium (BE) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Belgium (BE) | Toll-free | ✅ | 🟡 | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Belgium (BE) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Belize (BZ) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Belize (BZ) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Benin (BJ) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Bermuda (BM) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Bonaire (BQ) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Bolivia (BO) | DID | ✅(1) | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Bosnia and Herzegovina (BA) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Bosnia and Herzegovina (BA) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Botswana (BW) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Brazil (BR) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | us-east-1, us-west-2 | GA - Via Partner |
| Brazil (BR) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA - Via Partner |
| Brazil (BR) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| British Virgin Islands (VG) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Brunei (BN) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Bulgaria (BG) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Bulgaria (BG) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Burkina Faso (BF) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Cambodia (KH) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Cambodia (KH) | Toll-free | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Cameroon (CM) | DID | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Canada (CA) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | ca-central-1 | GA |
| Canada (CA) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | ca-central-1 | GA |
| Canada (CA) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Cayman Islands (KY) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Chile (CL) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Chile (CL) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| China (CN) | Outbound | ❌ | ❌ | 🟡(1) | ❌ | ❌ | ❌ | All regions | — | GA |
| China (CN) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Colombia (CO) | DID | ✅ | 🟡(2) | ✅ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Colombia (CO) | Toll-free | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Colombia (CO) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Costa Rica (CR) | DID | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Costa Rica (CR) | Toll-free | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Costa Rica (CR) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Croatia (HR) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Croatia (HR) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Cuba (CU) | Toll-free | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Curaçao (CW) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Cyprus (CY) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Cyprus (CY) | Toll-free | ✅ | 🟡 | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Czech Republic (CZ) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | All commercial | — | GA |
| Czech Republic (CZ) | Toll-free | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | All commercial | — | GA |
| Denmark (DK) | DID (mobile) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Denmark (DK) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Denmark (DK) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Denmark (DK) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Dominica (DM) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Dominica (DM) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Dominican Republic (DO) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Dominican Republic (DO) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Ecuador (EC) | DID | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Ecuador (EC) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Egypt (EG) | DID | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA - Via Partner |
| Egypt (EG) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA - Via Partner |
| El Salvador (SV) | DID | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | All commercial | — | GA |
| El Salvador (SV) | Toll-free | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Estonia (EE) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | All commercial | — | GA |
| Estonia (EE) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Estonia (EE) | Toll-free | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | All commercial | — | GA |
| Ethiopia (ET) | DID | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Finland (FI) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Finland (FI) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Fiji (FJ) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| France (FR) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| France (FR) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| France (FR) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| French Guiana (GF) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| French Guiana (GF) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Georgia (GE) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Germany (DE) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Germany (DE) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Germany (DE) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Ghana (GH) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Ghana (GH) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Greece (GR) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | — | GA |
| Greece (GR) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | — | GA |
| Greece (GR) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Grenada (GD) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Guadeloupe (GP) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Guadeloupe (GP) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Guatemala (GT) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Guam (GU) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Honduras (HN) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Honduras (HN) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Hong Kong (HK) | DID | ✅ | 🟡(1) | ✅ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Hong Kong (HK) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Hong Kong (HK) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Hungary (HU) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | All commercial | — | GA |
| Hungary (HU) | Toll-free | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | All commercial | — | GA |
| Hungary (HU) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Iceland (IS) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Iceland (IS) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Iceland (IS) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| India (IN) | DID | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| India (IN) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Indonesia (ID) | DID | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Indonesia (ID) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA - Via Partner |
| Ireland (IE) | DID | ✅(1) | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Ireland (IE) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Israel (IL) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | GA - Via Partner |
| Israel (IL) | Toll-free | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA - Via Partner |
| Israel (IL) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Italy (IT) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Italy (IT) | Toll-free | ✅ | 🟡 | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Italy (IT) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Ivory Coast (CI) | DID | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Ivory Coast (CI) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Jamaica (JM) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Japan (JP) | DID | ✅(2) | ✅ | ✅ | 🟡(1) | ✅ | ❌ | ap-northeast-1 | ap-northeast-1 | GA |
| Japan (JP) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | ap-northeast-1 | GA |
| Japan (JP) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | All commercial | ap-northeast-1 | GA |
| Japan (JP) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Jordan (JO) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Jordan (JO) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Kazakhstan (KZ) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Kazakhstan (KZ) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Kyrgyzstan (KG) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Kenya (KE) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Kenya (KE) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Kosovo (XK) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Kuwait (KW) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Laos (LA) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Latvia (LV) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Latvia (LV) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Latvia (LV) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Lebanon (LB) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Lesotho (LS) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Liechtenstein (LI) | Toll-free | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Lithuania (LT) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Lithuania (LT) | Toll-free | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Lithuania (LT) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Luxembourg (LU) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Luxembourg (LU) | Toll-free | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Luxembourg (LU) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Macao (MO) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Macao (MO) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Macedonia (MK) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Macedonia (MK) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Malaysia (MY) | DID | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | All commercial | ap-southeast-1 | GA |
| Malaysia (MY) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Malawi (MW) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Malta (MT) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | Partner BETA |
| Malta (MT) | Toll-free | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Martinique (MQ) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Martinique (MQ) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Mauritius (MU) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Mauritius (MU) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Mayotte (YT) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Mayotte (YT) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Mexico (MX) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | us-east-1, us-west-2 | GA |
| Mexico (MX) | Toll-free | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Moldova (MD) | DID | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Moldova (MD) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Monaco (MC) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Monaco (MC) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Mongolia (MN) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Montenegro (ME) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Montserrat (MS) | Toll-free | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Morocco (MA) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Mozambique (MZ) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Myanmar (MM) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Nepal (NP) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Netherlands (NL) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Netherlands (NL) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Netherlands (NL) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| New Zealand (NZ) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | ap-southeast-2 | GA |
| New Zealand (NZ) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | ap-southeast-2 | GA |
| New Zealand (NZ) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Nicaragua (NI) | DID | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Nigeria (NG) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Testing |
| Norway (NO) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | eu-central-1, eu-west-2 | — | GA |
| Norway (NO) | Toll-free | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | eu-central-1, eu-west-2 | — | GA |
| Northern Mariana (MP) | Toll-free | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Oman (OM) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Pakistan (PK) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Pakistan (PK) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Panama (PA) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Panama (PA) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Papua New Guinea (PG) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Paraguay (PY) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Paraguay (PY) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Peru (PE) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Peru (PE) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Peru (PE) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Philippines (PH) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ap-southeast-1 | ap-southeast-1 | Preview |
| Philippines (PH) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ap-southeast-1 | — | Preview |
| Philippines (PH) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Poland (PL) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Poland (PL) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Portugal (PT) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Portugal (PT) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Portugal (PT) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Puerto Rico (PR) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | us-east-1, us-west-2 | GA |
| Puerto Rico (PR) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | — | GA |
| Qatar (QA) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Qatar (QA) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Reunion (RE) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Reunion (RE) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Romania (RO) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Romania (RO) | Toll-free | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Romania (RO) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Russia (RU) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Rwanda (RW) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Saba (BQ) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Saint Kitts and Nevis (KN) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Saint Kitts and Nevis (KN) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Saint Lucia (LC) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Saint Martin (MF) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Saint Pierre and Miquelon (PM) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Saint Pierre and Miquelon (PM) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Saint Vincent Grenadines (VC) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Saint Vincent Grenadines (VC) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Saudi Arabia (SA) | Toll-free | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA - Via Partner |
| Sint Eustatius (BQ) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Sint Maarten (SX) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Serbia (RS) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Serbia (RS) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Seychelles (SC) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Sierra Leone (SL) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Singapore (SG) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | All commercial | ap-southeast-1 | GA |
| Singapore (SG) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Singapore (SG) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Slovakia (SK) | DID | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | All commercial | — | GA |
| Slovakia (SK) | Toll-free | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ | All commercial | — | GA |
| Slovakia (SK) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Slovenia (SI) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | — | GA |
| Slovenia (SI) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | — | GA |
| South Africa (ZA) | DID (mobile) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | af-south-1 | — | GA |
| South Africa (ZA) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | af-south-1 | af-south-1 | GA |
| South Africa (ZA) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | af-south-1 | af-south-1 | GA |
| South Africa (ZA) | Shared Cost | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | af-south-1 | — | GA |
| South Africa (ZA) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| South Korea (KR) | DID | 🟡(1) | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | ap-northeast-2 | GA |
| South Korea (KR) | Toll-free | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| South Korea (KR) | Representative | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | All commercial | ap-northeast-2 | GA |
| South Korea (KR) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Spain (ES) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| Spain (ES) | Toll-free | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Spain (ES) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Sri Lanka (LK) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Sri Lanka (LK) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Sudan (SD) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Sweden (SE) | DID (mobile) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Sweden (SE) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | — | GA |
| Sweden (SE) | Toll-free | ✅ | 🟡 | ❌ | ✅ | ✅ | ❌ | All commercial | — | GA |
| Switzerland (CH) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | — | GA |
| Switzerland (CH) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | — | GA |
| Switzerland (CH) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Tanzania (TZ) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Tanzania (TZ) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Taiwan (TW) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Taiwan (TW) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Thailand (TH) | DID | ✅ | 🟡(2) | ✅ | ✅ | ✅ | ❌ | All commercial | ap-southeast-1 | GA |
| Thailand (TH) | Toll-free | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | All commercial | — | GA |
| Thailand (TH) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Trinidad and Tobago (TT) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Tunisia (TN) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Turkey (TR) | DID | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | Partner GA |
| Turkey (TR) | Toll-free | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | Partner GA |
| Turks and Caicos (TC) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Uganda (UG) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Uganda (UG) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Ukraine (UA) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner GA |
| Ukraine (UA) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner GA |
| United Arab Emirates (AE) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| United Arab Emirates (AE) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA - Via Partner |
| United Kingdom (GB) | DID (mobile) | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | All commercial | — | GA |
| United Kingdom (GB) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| United Kingdom (GB) | Toll-free | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | All commercial | eu-central-1, eu-west-2 | GA |
| United Kingdom (GB) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| United States (US) | DID | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All regions | us-east-1, us-west-2 | GA |
| United States (US) | Toll-free | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | All regions | us-east-1, us-west-2 | GA |
| Uzbekistan (UZ) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Uruguay (UY) | Outbound | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | All regions | — | GA |
| Uruguay (UY) | UIFN | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | All commercial | — | GA |
| Venezuela (VE) | DID | 🟡(1) | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Venezuela (VE) | Toll-free | 🟡 | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA |
| Vietnam (VN) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | GA - Via Partner |
| Vietnam (VN) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | GA - Via Partner |
| Virgin Islands (UK) (VG) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Virgin Islands (US) (VI) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Virgin Islands (US) (VI) | Toll-free | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Zambia (ZM) | DID | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |
| Zimbabwe (ZW) | DID | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | All commercial | — | Partner BETA |

Footnotes from the guide:

- (1) When calling Bahrain, a mandatory welcome message is played to customers to enforce regulatory requirements
- (1) Bolivia DID numbers in our offering are designed for domestic inbound use. International reachability is not guaranteed
- (1) China has international outbound call restrictions
- (2) Colombia we have one of our two networks in country, if you need National outbound please ensure you specify this
- (1) Hong Kong we have one of our two networks in country, if you need National outbound please ensure you specify this
- (1) National Numbers in Ireland do not support Outbound Campaigns
- (2) Local Numbers and Porting in Japan is only possible on specific numbers
- (1) New local DID's in Korea need to be physically installed at customer site for 6 months prior to porting
- (2) Thailand we have one of our two networks in country, if you need National outbound please ensure you specify this
- (1) Venezuelan DID and Toll-Free Inbound have partial national reachability

## 6. Countries with Region-restricted ordering or agent-location rules (phone-number requirements page)

Default rule: "All AWS Regions are supported—except Africa (Cape Town) and AWS GovCloud (US-West)—unless noted otherwise"

| Country | Number | Supported Regions | Agent location |
|---|---|---|---|
| Japan (JP) | Local telephone numbers: +81 3, +81 6 | ap-northeast-1 | — |
| Japan (JP) | Local number prefixes: +81 50 | All | — |
| Japan (JP) | Toll-free prefixes: +81 120, +81 800 | All | — |
| Nigeria (NG) | Local telephone numbers | af-south-1 | — |
| Norway (NO) | Local telephone numbers: | eu-central-1, eu-west-2 | — |
| Norway (NO) | Toll-free prefixes: +47 800 | eu-central-1, eu-west-2 | — |
| Norway (NO) | National prefixes: +47 81, +47 85 | eu-central-1, eu-west-2 | — |
| Philippines (PH) | Local telephone numbers: +63 2 | default rule | The agent must be located within the Philippines. |
| Philippines (PH) | Toll-free prefixes:+63 1800 | default rule | The agent must be located within the Philippines. |
| Uganda (UG) | Local telephone numbers | af-south-1 | — |
| Uganda (UG) | Toll-free prefixes | af-south-1 | — |
| Vietnam (VN) | Local telephone numbers | default rule | The agent must be located within Vietnam. |
| Vietnam (VN) | Toll-free prefixes: +84 1800, +84 1900 | default rule | The agent must be located within Vietnam. |
| South Africa (ZA) | Local numbers: | af-south-1 | — |
| South Africa (ZA) | Mobile numbers: | af-south-1 | — |
| South Africa (ZA) | Toll-free prefixes: +27 80 | af-south-1 | — |
| South Africa (ZA) | Shared-Cost prefixes: +27 860, +27 861 | af-south-1 | — |

## Sources

- `regions` — https://docs.aws.amazon.com/connect/latest/adminguide/regions.html (retrieved 2026-10-06)
- `telecoms_pdf` — https://d1v2gagwb6hfe1.cloudfront.net/Amazon_Connect_Telecoms_Coverage.pdf (retrieved 2026-10-06)
- `number_requirements` — https://docs.aws.amazon.com/connect/latest/adminguide/phone-number-requirements.html (retrieved 2026-10-06)
- `default_outbound` — https://docs.aws.amazon.com/connect/latest/adminguide/country-code-allow-list.html (retrieved 2026-10-06)
- `gr_replica` — https://docs.aws.amazon.com/connect/latest/adminguide/create-replica-connect-instance.html (retrieved 2026-10-06)
- `gr_requirements` — https://docs.aws.amazon.com/connect/latest/adminguide/connect-global-resiliency-requirements.html (retrieved 2026-10-06)
- `low_latency` — https://docs.aws.amazon.com/connect/latest/adminguide/low-latency-design.html (retrieved 2026-10-06)
- `region_selection` — https://docs.aws.amazon.com/connect/latest/adminguide/operational-excellence.html (retrieved 2026-10-06)
- `single_vs_multi_instance` — https://docs.aws.amazon.com/connect/latest/adminguide/single-instance-multiple-instances.html (retrieved 2026-10-06)
- `supported_languages` — https://docs.aws.amazon.com/connect/latest/adminguide/supported-languages.html (retrieved 2026-10-06)
- `endpoint_test_utility` — https://docs.aws.amazon.com/connect/latest/adminguide/check-connectivity-tool.html (retrieved 2026-10-06)
