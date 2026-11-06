// Halaman semakan IAA. Teks dokumen dimasukkan sebagai nod teks sahaja (tiada HTML mentah). Setiap ketikan = satu POST.
"use strict";
(() => {
  const asas = location.pathname.replace(/\/+$/, "");
  const $ = (s, el = document) => el.querySelector(s);
  let t = {};          // teks bahasa semasa
  let k = null;        // keadaan terakhir dari pelayan
  let sibuk = false;

  const isi = (str, v) => str.replace(/\{(\w+)\}/g, (_, n) => v[n]);

  function terjemah(akar) {
    akar.querySelectorAll("[data-t]").forEach((el) => { el.textContent = t[el.dataset.t] || ""; });
  }

  async function muatBahasa(b) {
    let r = await fetch(`/teks/${encodeURIComponent(b)}.json`, { cache: "no-store" });
    if (!r.ok) r = await fetch("/teks/ms.json", { cache: "no-store" });
    t = await r.json();
    document.documentElement.lang = t.bahasa;
    try { localStorage.setItem("mypii-iaa-bahasa", t.bahasa); } catch (_) { /* mod peribadi */ }
    const bb = $("#bahasa");
    bb.textContent = t.tukar_bahasa;
    bb.setAttribute("aria-label", t.tukar_bahasa_label);
    terjemah(document);
    status(...statusKini);
    if (k) lukis(false);
  }

  let statusKini = ["", false];   // kunci teks, bukan teks — ditulis semula bila bahasa bertukar

  function status(kunci, ralat) {
    statusKini = [kunci, !!ralat];
    const s = $("#status");
    s.textContent = kunci ? t[kunci] || "" : "";
    s.classList.toggle("ralat", !!ralat);
  }

  async function panggil(kaedah, laluan, badan) {
    const r = await fetch(asas + laluan, {
      method: kaedah, cache: "no-store",
      headers: badan ? { "Content-Type": "application/json" } : {},
      body: badan ? JSON.stringify(badan) : undefined,
    });
    if (!r.ok) throw new Error(String(r.status));
    return r.json();
  }

  function butang(kelas, label, ditekan, onklik) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = kelas;
    b.textContent = label;
    b.setAttribute("aria-pressed", ditekan ? "true" : "false");
    b.addEventListener("click", onklik);
    return b;
  }

  function lukisTeks(el, d) {
    let i = 0;
    d.spans.forEach((s, n) => {
      if (s.mula > i) el.append(document.createTextNode(d.teks.slice(i, s.mula)));
      const m = document.createElement("mark");
      m.className = `m m-${s.entiti}`;
      m.append(document.createTextNode(d.teks.slice(s.mula, s.tamat)));
      const no = document.createElement("sup");
      no.textContent = String(n + 1);
      no.setAttribute("aria-label", `${t.jenis[s.entiti] || s.entiti} ${n + 1}`);
      m.append(no);
      el.append(m);
      i = Math.max(i, s.tamat);
    });
    if (i < d.teks.length) el.append(document.createTextNode(d.teks.slice(i)));
  }

  async function jawab(soalan, nilai, el) {
    if (sibuk || !k || !k.dokumen) return;
    sibuk = true;
    if (el) el.classList.add("hantar");
    try {
      k = await panggil("POST", "/jawab", { urutan: k.dokumen.urutan, soalan, nilai });
      status("disimpan");
      lukis(false);
    } catch (_) {
      status("ralat_simpan", true);
      if (el) el.classList.remove("hantar");
    } finally { sibuk = false; }
  }

  function lukisDokumen(utama, d) {
    utama.append($("#t-dokumen").content.cloneNode(true));
    terjemah(utama);
    $(".helaian-no", utama).textContent = isi(t.dokumen, { u: d.urutan });
    lukisTeks($(".teks", utama), d);

    const senarai = $(".span-senarai", utama);
    if (!d.spans.length) {
      const li = document.createElement("li");
      li.className = "bantu";
      li.textContent = t.tiada_span;
      senarai.append(li);
      $(".soalan .bantu", utama).hidden = true;
    }
    d.spans.forEach((s, n) => {
      const sk = `a${n + 1}`;
      const li = document.createElement("li");
      li.className = "span-baris";
      const kep = document.createElement("div");
      kep.className = "span-kepala";
      const no = document.createElement("span"); no.className = "span-no"; no.textContent = String(n + 1);
      const jenis = document.createElement("span"); jenis.className = `span-jenis m-${s.entiti}`;
      jenis.textContent = t.jenis[s.entiti] || s.entiti;
      const nilai = document.createElement("span"); nilai.className = "span-nilai";
      nilai.textContent = d.teks.slice(s.mula, s.tamat);
      kep.append(no, jenis, nilai);
      const seg = document.createElement("div");
      seg.className = "segmen"; seg.setAttribute("role", "group");
      seg.setAttribute("aria-label", `${n + 1} ${jenis.textContent}`);
      k.pilihan.a.forEach((p) => seg.append(
        butang("pilihan", t.pilih_a[p], d.jawapan[sk] === p, (e) => jawab(sk, p, e.currentTarget))));
      li.append(kep, seg);
      senarai.append(li);
    });

    const jb = d.jawapan.b, [tiada, ada] = k.pilihan.b;
    const kotak = $(".kotak-b", utama), ta = $("textarea", kotak);
    const segB = $(".segmen-b", utama);
    segB.append(
      butang("pilihan", t.pilih_b[tiada], jb && jb.pilih === tiada, (e) => jawab("b", { pilih: tiada }, e.currentTarget)),
      butang("pilihan", t.pilih_b[ada], (jb && jb.pilih === ada), (e) => {
        kotak.hidden = false;
        e.currentTarget.setAttribute("aria-pressed", "true");
        e.currentTarget.previousSibling.setAttribute("aria-pressed", "false");
        ta.focus();
      }));
    if (jb && jb.pilih === ada) { kotak.hidden = false; ta.value = jb.nilai.join("\n"); }
    $(".butang-simpan", kotak).addEventListener("click", (e) => {
      const baris = ta.value.split("\n").map((x) => x.trim()).filter(Boolean);
      if (!baris.length) { status("b_kosong", true); ta.focus(); return; }
      jawab("b", { pilih: ada, nilai: baris.slice(0, k.had_nilai_b) }, e.currentTarget);
    });

    const segC = $(".segmen-c", utama);
    k.pilihan.c.forEach((p) => segC.append(
      butang("pilihan", t.pilih_c[p], d.jawapan.c === p, (e) => jawab("c", p, e.currentTarget))));
  }

  function lukis(fokus) {
    const utama = $("#utama");
    const y = window.scrollY;
    utama.replaceChildren();
    const peratus = k.n ? Math.round((k.siap / k.n) * 100) : 0;
    $("#kemajuan-isi").style.width = `${peratus}%`;
    const bar = $("#kemajuan");
    bar.setAttribute("aria-valuemax", String(k.n));
    bar.setAttribute("aria-valuenow", String(k.siap));
    $("#kemajuan-teks").textContent = isi(t.kemajuan, { siap: k.siap, n: k.n });

    const d = k.dokumen;
    if (d) lukisDokumen(utama, d);
    else { utama.append($("#t-tamat").content.cloneNode(true)); terjemah(utama); }

    const undur = $("#undur");
    undur.textContent = t.undur;
    undur.setAttribute("aria-label", t.undur_label);
    undur.disabled = !k.boleh_undur;
    const seterusnya = $("#seterusnya");
    seterusnya.textContent = t.seterusnya;
    seterusnya.hidden = !d;
    seterusnya.disabled = !(d && d.siap);
    seterusnya.title = d && !d.siap ? t.belum_siap : "";
    if (fokus) { window.scrollTo(0, 0); utama.focus({ preventScroll: true }); } else window.scrollTo(0, y);
  }

  async function seterusnya() {
    if (sibuk) return;
    sibuk = true;
    try { k = await panggil("GET", "/keadaan"); status(""); lukis(true); }
    catch (_) { status("ralat_simpan", true); }
    finally { sibuk = false; }
  }

  async function undur() {
    if (sibuk) return;
    sibuk = true;
    try {
      const lama = k && k.dokumen ? k.dokumen.urutan : null;
      k = await panggil("POST", "/undur", {});
      status("dibatalkan");
      lukis(!k.dokumen || k.dokumen.urutan !== lama);
    } catch (_) { status("ralat_simpan", true); }
    finally { sibuk = false; }
  }

  async function mula() {
    let b = "ms";
    try { b = localStorage.getItem("mypii-iaa-bahasa") || b; } catch (_) { /* mod peribadi */ }
    await muatBahasa(b);
    $("#bahasa").addEventListener("click", () => muatBahasa(t.bahasa === "ms" ? "en" : "ms"));
    $("#undur").addEventListener("click", undur);
    $("#seterusnya").addEventListener("click", seterusnya);
    try { k = await panggil("GET", "/keadaan"); lukis(false); }
    catch (_) { status("ralat_simpan", true); }
  }
  mula();
})();
