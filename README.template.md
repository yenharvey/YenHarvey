<!-- 此文件由 scripts/build_readme.py 生成 README.md，请改 README.template.md，不要直接改 README.md -->
<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/banner-dark.svg">
  <img src="./assets/banner-light.svg" alt="Yen Harvey — Rust · AI applications · Full-stack" width="100%">
</picture>

<p>
  <a href="https://yenharvey.com"><img src="https://img.shields.io/badge/Blog-yenharvey.com-F97316?style=for-the-badge&logo=rss&logoColor=white" alt="Blog"></a>
  <a href="https://acghub.net"><img src="https://img.shields.io/badge/ACGHub-acghub.net-FF69B4?style=for-the-badge&logo=home&logoColor=white" alt="ACGHub"></a>
  <a href="https://qingjian.app"><img src="https://img.shields.io/badge/Qingjian-qingjian.app-2EA043?style=for-the-badge&logo=rust&logoColor=white" alt="Qingjian"></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Rust-000000?style=flat-square&logo=rust&logoColor=white" alt="Rust">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Svelte-FF3E00?style=flat-square&logo=svelte&logoColor=white" alt="Svelte">
  <img src="https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/Flutter-02569B?style=flat-square&logo=flutter&logoColor=white" alt="Flutter">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Cloudflare_Workers-F38020?style=flat-square&logo=cloudflare&logoColor=white" alt="Cloudflare Workers">
  <img src="https://img.shields.io/badge/WebAssembly-654FF0?style=flat-square&logo=webassembly&logoColor=white" alt="WebAssembly">
  <img src="https://img.shields.io/badge/C%23_%2F_.NET-512BD4?style=flat-square&logo=dotnet&logoColor=white" alt="C# / .NET">
</p>

</div>

## 👋 About

I build production software end to end: Rust backends, TypeScript / Svelte frontends, Flutter mobile clients, and the infrastructure around them. My degree is in AI application, and my day job is building LLM agents for finance and ERP workflows. On the side I run **[ACGHub](https://acghub.net)**, a community platform I have designed, written and operated alone since 2024, and I am writing **[Qingjian](https://qingjian.app)**, a pinyin input method in Rust.

Most of my code lives in private repositories, so the projects below come with their scale instead of a link. The numbers are regenerated weekly from the repositories themselves.

## 🖥 Showcase

<table>
  <tr>
    <td width="50%" align="center">
      <a href="https://acghub.net"><img src="./assets/acghub.webp" alt="ACGHub home feed"></a><br>
      <sub><b>ACGHub</b> · community feed, tags, weekly anime schedule</sub>
    </td>
    <td width="50%" align="center">
      <a href="https://qingjian.app"><img src="./assets/qingjian.webp" alt="Qingjian landing page"></a><br>
      <sub><b>Qingjian 青简</b> · input method that teaches a word per keystroke</sub>
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="./assets/studio.webp" alt="ACGHub Studio storyboard canvas"><br>
      <sub><b>ACGHub Studio</b> · script-to-storyboard workbench, two-page spread canvas with pacing strip</sub>
    </td>
  </tr>
</table>

## 🏗 ACGHub at a glance

One person, one platform, twelve repositories. Everything below is written and operated by me.

```mermaid
flowchart LR
  subgraph clients [Clients]
    direction TB
    web["acghub-web<br/>SvelteKit"]
    app["acghub-app<br/>Flutter · iOS / Android"]
    admin["acghub-admin<br/>Angular"]
    studio["acghub-studio<br/>SvelteKit · WIP"]
  end

  guard["api-guard<br/>Rust + WASM<br/>ECDH · HMAC · PoW · rate limit"]
  server["acghub-server<br/>Rust · Axum · PostgreSQL"]
  luna["luna-pass<br/>SSO · OAuth · RBAC"]
  geo["acghub-geo<br/>GeoIP · ASN"]
  link["acghub-link<br/>short links"]
  static["acghub-static<br/>brand assets · CDN"]
  status["acghub-status<br/>Cloudflare Workers"]

  web --> guard --> server
  app --> server
  admin --> server
  studio -.-> server
  server --> luna
  server --> geo
  server --> link
  web --> static
  status -. monitors .-> server
```

## 🚀 Selected work

| Project | Stack | Status | Scale | What it is |
|---|---|:---:|---|---|
| **ACGHub** <br> [acghub.net](https://acghub.net) | ![Rust](https://img.shields.io/badge/-Rust-000?logo=rust&logoColor=white) ![Axum](https://img.shields.io/badge/-Axum-000) ![SvelteKit](https://img.shields.io/badge/-SvelteKit-FF3E00?logo=svelte&logoColor=white) ![Flutter](https://img.shields.io/badge/-Flutter-02569B?logo=flutter&logoColor=white) | ![live](https://img.shields.io/badge/-live-2EA043) | **{{acghub.commits}} commits** <br> {{acghub.lines}} <br> {{acghub.lines.dart}} Dart | Tag-driven community platform for anime, comics and games. Backend, web, mobile app, admin console, static CDN, status page and short-link service, all one person. |
| **ACGHub API Guard** | ![Rust](https://img.shields.io/badge/-Rust-000?logo=rust&logoColor=white) ![WASM](https://img.shields.io/badge/-WebAssembly-654FF0?logo=webassembly&logoColor=white) | ![live](https://img.shields.io/badge/-live-2EA043) | {{api_guard.lines}} | Browser-to-server request integrity layer: ECDH session keys, HMAC canonical requests, nonce + timestamp windows, proof-of-work handshake, multi-dimension rate limiting. Turns "one `curl` line" into "days of reverse engineering". |
| **Luna-Pass** | ![Rust](https://img.shields.io/badge/-Rust-000?logo=rust&logoColor=white) ![SeaORM](https://img.shields.io/badge/-SeaORM-000) | ![live](https://img.shields.io/badge/-live-2EA043) | {{luna_pass.lines}} | Unified auth and SSO across all ACGHub subdomains: local accounts, OAuth (GitHub / Google), opaque-token sessions, RBAC with role inheritance. |
| **ACGHub Studio** | ![SvelteKit](https://img.shields.io/badge/-SvelteKit-FF3E00?logo=svelte&logoColor=white) ![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white) | ![wip](https://img.shields.io/badge/-WIP-F97316) | frontend MVP | Script-to-storyboard (ネーム) workbench for comic authors: prose script in, editable paged panels out. Two-page spread canvas with RTL reading order, a pacing strip that plots panel density and page-turn hooks, procedural composition sketches from shot type, camera and cast. Rust backend next. |
| **Qingjian 青简** <br> [repo](https://github.com/qingjian-team/qingjian) · [qingjian.app](https://qingjian.app) | ![Rust](https://img.shields.io/badge/-Rust-000?logo=rust&logoColor=white) | ![oss](https://img.shields.io/badge/-open_source-3178C6) | {{qingjian.lines}} | Cross-platform pinyin input method that shows a translation next to each candidate in the language you are learning. Fully local: dictionary, learning state and n-gram all on device. macOS beta. |
| **Bling Atelier** | ![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white) ![Rust](https://img.shields.io/badge/-Rust-000?logo=rust&logoColor=white) | ![private](https://img.shields.io/badge/-private-6E7681) | {{bling.lines}} | AI product-image generation fused with a lightweight ERP (SPU / SKU, assets, render history, inventory) for apparel sellers. |
| **Bank receipt RPA** | ![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white) | ![private](https://img.shields.io/badge/-private-6E7681) | {{zyra.lines}} | Automated download and archival of bank receipts from multiple Chinese banks, with task queue, dashboard and object-storage upload. Built for finance operations at work. |

<sub>Lines are code only (tokei, no config / markup / vendored code). Updated {{updated_at}}.</sub>

## 📦 Open source

| Repo | What |
|---|---|
| [qingjian-team/qingjian](https://github.com/qingjian-team/qingjian) | Rust input method engine described above |
| [my-axum-starter](https://github.com/yenharvey/my-axum-starter) | Axum project template with the conventions I use in production |
| [qq-bot-rs](https://github.com/yenharvey/qq-bot-rs) | QQ bot SDK in Rust |
| [tencent-sdk-unofficial](https://github.com/yenharvey/tencent-sdk-unofficial) | Typed Rust client for Tencent Cloud APIs |
| [aliyun-dypns](https://github.com/yenharvey/aliyun-dypns) | Rust SDK for Aliyun SMS verification |
| [tieba-sign](https://github.com/yenharvey/tieba-sign) | Baidu Tieba check-in CLI |
| [mygo-studio/anon-flatten](https://github.com/mygo-studio/anon-flatten) | Directory flattening tool |
| [yahboom_gps](https://github.com/yenharvey/yahboom_gps) | Serial GPS driver for a Yahboom module |

## 🛠 Skills

- **Rust** — primary language. Axum, Tokio, SeaORM, WASM, CLI tooling, SDK design. Comfortable owning a 200k-line codebase alone.
- **AI applications** — LLM agents, tool use, multi-agent orchestration, RAG. Finance and ERP agents in production at work.
- **Web** — TypeScript, SvelteKit, Next.js, Cloudflare Workers. Flutter for mobile.
- **Python** — automation, RPA, data pipelines, FastAPI.
- **Infrastructure** — PostgreSQL, Docker, GitHub Actions, CDN and edge deployment, Tencent Cloud and Aliyun.
- **Learning** — C# and .NET.

## 🧭 Now

- Writing Qingjian, the Rust input method above. Currently macOS beta.
- Building a finance / ERP agent at work, plus the full-stack around it.
- Running and growing ACGHub; getting Studio from mock data to a Rust backend.

## ✍️ Writing

Latest from [yenharvey.com](https://yenharvey.com):

{{blog_posts}}

## 📈 Languages

<!-- 设置 METRICS_TOKEN secret 并重跑 Metrics workflow 后，取消下面这段注释
Across all repositories I own or contribute to, private and organization repos included:

<img src="./metrics.languages.svg" alt="Languages and lines of code" width="100%">
-->
