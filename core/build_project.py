"""Rakit paket Claude Project dari 4 lapis ATA (core, domain, method, instance).

Pemakaian:
    python3 scripts/build_project.py <kode-tesis> [--out DIR]   paket untuk satu tesis (dikelola tim)
    python3 scripts/build_project.py --starter [--out DIR]       starter kit umum (self-service)

Hasil di build/<kode-tesis>/:
    project-instructions.md   tempel ke Project instructions
    knowledge/                unggah ke knowledge Project
    peran/                    prompt per peran, tempel sebagai pesan pertama chat
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_KEYS = (
    "kode", "jenjang_prodi", "persona", "jam_per_minggu",
    "pembimbing", "kode_sesi", "topik", "domain", "method_packs",
)
# [BARU MULTI-USER] Kunci opsional: tidak semua tesis punya organisasi kasus, prodi profile, atau berbahasa Indonesia.
DEFAULTS = {
    "lembaga_kasus": "pengguna hasil penelitian",
    "peneliti_orang_dalam": False,
    "bahasa_tesis": "Indonesia",
    "tenggat": "belum ditentukan",
    "prodi": None,
}
INSIDER_SENTENCE = (
    "Mahasiswa bekerja di {lembaga}, sehingga berstatus peneliti orang dalam; "
    "posisi ini, potensi biasnya, dan izin organisasi wajib dibahas di bab Metode."
)
CLASSIFICATION_FILE = "klasifikasi-lembaga.md"
PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")
ROLE_HEADING = re.compile(r"^## Peran: *([a-z0-9-]+) *$", re.MULTILINE)
UNFILLED_MARK = "[isi"
INSTANCE_FILES = ("00-ledger.md", "01-profil-tesis.md", "02-matriks-konsistensi.md", "05-sampel-tulisan.md")


class ConfigError(ValueError):
    """tesis.yaml tidak lengkap atau merujuk lapis yang tidak ada."""


def render(text, values):
    """Ganti {{kunci}} dengan nilai; list digabung dengan koma. Kunci tak dikenal dibiarkan."""
    def replace(match):
        value = values.get(match.group(1))
        if value is None:
            return match.group(0)
        return ", ".join(map(str, value)) if isinstance(value, list) else str(value)
    return PLACEHOLDER.sub(replace, text)


def with_defaults(config):
    """Kembalikan salinan config dengan nilai bawaan dan nilai turunan (tanpa mengubah input)."""
    merged = {**DEFAULTS, **{k: v for k, v in config.items() if v is not None}}
    insider = bool(merged["peneliti_orang_dalam"])
    sentence = INSIDER_SENTENCE.format(lembaga=merged["lembaga_kasus"]) if insider else ""
    return {**merged, "konteks_peneliti": sentence}


def strip_comments(text):
    return re.sub(r"<!--.*?-->\s*", "", text, flags=re.DOTALL)


def unresolved(text):
    return PLACEHOLDER.findall(text)


def split_roles(markdown):
    """Pecah file berisi '## Peran: <nama>' jadi {nama: isi bagian}."""
    matches = list(ROLE_HEADING.finditer(markdown))
    roles = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        body = markdown[match.end():end]
        roles[match.group(1)] = re.split(r"^## ", body, flags=re.MULTILINE)[0].strip()
    return roles


def section(markdown, heading):
    """Ambil isi bagian '## <heading>' sampai heading level-2 berikutnya."""
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(markdown)
    return match.group(1).strip() if match else ""


def load_instance(code, root=ROOT):
    path = root / "instances" / code / "tesis.yaml"
    if not path.exists():
        raise ConfigError(f"Instance tidak ditemukan: {path}")
    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    validate_config(config, root)
    return config


def validate_config(config, root=ROOT):
    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise ConfigError(f"tesis.yaml kurang kunci: {', '.join(missing)}")
    if not (root / "domain" / f"{config['domain']}.md").exists():
        raise ConfigError(f"Domain Profile tidak ada: domain/{config['domain']}.md")
    packs = config["method_packs"]
    if not isinstance(packs, list) or not packs:
        raise ConfigError("method_packs harus list berisi minimal satu pack")
    absent = [pack for pack in packs if not (root / "method" / f"{pack}.md").exists()]
    if absent:
        raise ConfigError(f"Method Pack tidak ada: {', '.join(absent)}")
    prodi = config.get("prodi")
    if prodi and not (root / "prodi" / f"{prodi}.md").exists():
        raise ConfigError(f"Prodi Profile tidak ada: prodi/{prodi}.md")


def unfilled_keys(config):
    return [key for key, value in config.items() if isinstance(value, str) and UNFILLED_MARK in value]


def merged_phrases(root, domain_text):
    core = (root / "core" / "frasa-terlarang.md").read_text(encoding="utf-8")
    extra = section(domain_text, "Frasa terlarang tambahan")
    return f"{core.rstrip()}\n\n## Tambahan dari Domain Profile\n\n{extra}\n" if extra else core


def knowledge_files(config, root):
    """Kembalikan {nama file: isi} untuk folder knowledge/."""
    instance_dir = root / "instances" / config["kode"]
    domain_text = (root / "domain" / f"{config['domain']}.md").read_text(encoding="utf-8")
    files = {
        name: (instance_dir / name).read_text(encoding="utf-8")
        for name in INSTANCE_FILES if (instance_dir / name).exists()
    }
    files["07-frasa-terlarang.md"] = merged_phrases(root, domain_text)
    if config.get("prodi"):
        files["08-prodi-profile.md"] = (root / "prodi" / f"{config['prodi']}.md").read_text(encoding="utf-8")
    files["09-domain-profile.md"] = domain_text
    for pack in config["method_packs"]:
        files[f"10-method-{pack}.md"] = (root / "method" / f"{pack}.md").read_text(encoding="utf-8")
    files["11-gates.md"] = (root / "core" / "gates.md").read_text(encoding="utf-8")
    files["12-data-intake.md"] = (root / "core" / "data-intake.md").read_text(encoding="utf-8")
    if (instance_dir / CLASSIFICATION_FILE).exists():
        files["13-klasifikasi-lembaga.md"] = (instance_dir / CLASSIFICATION_FILE).read_text(encoding="utf-8")
    return files


def role_files(config, root):
    sources = [root / "core" / "peran.md"] + [root / "method" / f"{p}.md" for p in config["method_packs"]]
    roles = {}
    for source in sources:
        roles = {**roles, **split_roles(source.read_text(encoding="utf-8"))}
    return {f"{name}.md": body for name, body in roles.items()}


def write_tree(base, files, config):
    base.mkdir(parents=True, exist_ok=True)
    leftovers = []
    for name, text in files.items():
        rendered = render(text, config)
        leftovers.extend(f"{base.name}/{name}: {key}" for key in unresolved(rendered))
        (base / name).write_text(rendered, encoding="utf-8")
    return leftovers


def build(code, root=ROOT, out_root=None):
    raw_config = load_instance(code, root)
    config = with_defaults(raw_config)
    package = (out_root or root / "build") / code
    if package.exists():
        shutil.rmtree(package)  # folder hasil generate; dibuat ulang agar tidak ada file usang
    instructions = render((root / "core" / "instruksi-global.md").read_text(encoding="utf-8"), config)
    instructions = strip_comments(instructions)
    package.mkdir(parents=True)
    (package / "project-instructions.md").write_text(instructions, encoding="utf-8")
    leftovers = [f"project-instructions.md: {key}" for key in unresolved(instructions)]
    leftovers += write_tree(package / "knowledge", knowledge_files(config, root), config)
    leftovers += write_tree(package / "peran", role_files(config, root), config)
    return {"package": package, "unresolved": leftovers, "unfilled": unfilled_keys(raw_config)}


# [BARU SELF-SERVICE] Starter kit: paket umum untuk pengguna yang mengoperasikan sendiri.
STARTER_REF = "[lihat 00-tesis.md]"
STARTER_VALUES = {
    **{key: STARTER_REF for key in REQUIRED_KEYS + tuple(DEFAULTS)},
    "kode_sesi": "<kode sesi>",
    "lembaga_kasus": "pengguna hasil penelitian (lihat 00-tesis.md)",
    "konteks_peneliti": (
        "Jika 00-tesis.md menyatakan peneliti_orang_dalam: true, mahasiswa berstatus peneliti orang dalam; "
        "posisi ini, potensi biasnya, dan izin organisasi wajib dibahas di bab Metode."
    ),
}
STARTER_PREFACE = (
    "Profil tesis ada di 00-tesis.md. Jika file itu masih berisi \"[isi]\", minta mahasiswa menjalankan "
    "peran mulai-di-sini (lihat PANDUAN) sebelum tugas lain.\n\n"
)
MODULE_FOLDERS = ("domain", "prodi", "method")


def profile_form(root):
    template = (root / "instances" / "_template" / "tesis.yaml").read_text(encoding="utf-8")
    return f"# Profil tesis\n\nDiisi lewat peran mulai-di-sini. Unggah ulang setelah diubah.\n\n```yaml\n{template}```\n"


def catalog(root):
    parts = [(root / folder / "README.md") for folder in ("domain", "method")]
    prodi = sorted(p.stem for p in (root / "prodi").glob("*.md") if not p.stem.startswith("_"))
    prodi_line = ", ".join(prodi) if prodi else "belum ada (opsional; buat dengan prodi-profile-builder)"
    body = "\n\n".join(p.read_text(encoding="utf-8") for p in parts if p.exists())
    return f"# KATALOG MODUL\n\n{body}\n\n# Prodi Profile tersedia\n\n{prodi_line}\n"


def starter_knowledge(root):
    template_dir = root / "instances" / "_template"
    files = {name: (template_dir / name).read_text(encoding="utf-8")
             for name in INSTANCE_FILES if (template_dir / name).exists()}
    return {
        **files,
        "00-tesis.md": profile_form(root),
        "07-frasa-terlarang.md": (root / "core" / "frasa-terlarang.md").read_text(encoding="utf-8"),
        "11-gates.md": (root / "core" / "gates.md").read_text(encoding="utf-8"),
        "12-data-intake.md": (root / "core" / "data-intake.md").read_text(encoding="utf-8"),
        "KATALOG.md": catalog(root),
    }


def starter_roles(root):
    roles = {}
    for name in ("peran.md", "onboarding.md"):
        roles = {**roles, **split_roles((root / "core" / name).read_text(encoding="utf-8"))}
    return {f"{name}.md": body for name, body in roles.items()}


def build_starter(root=ROOT, out_root=None):
    kit = (out_root or root / "build") / "starter-kit"
    if kit.exists():
        shutil.rmtree(kit)  # folder hasil generate
    kit.mkdir(parents=True)
    instructions = STARTER_PREFACE + strip_comments((root / "core" / "instruksi-global.md").read_text(encoding="utf-8"))
    (kit / "project-instructions.md").write_text(render(instructions, STARTER_VALUES), encoding="utf-8")
    (kit / "PANDUAN.md").write_text((root / "core" / "panduan-pengguna.md").read_text(encoding="utf-8"), encoding="utf-8")
    write_tree(kit / "knowledge", starter_knowledge(root), STARTER_VALUES)
    write_tree(kit / "peran", starter_roles(root), STARTER_VALUES)
    for folder in MODULE_FOLDERS:
        shutil.copytree(root / folder, kit / "modul" / folder)
    return kit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kode", nargs="?", help="kode instance (kosongkan jika memakai --starter)")
    parser.add_argument("--starter", action="store_true", help="buat starter kit umum untuk pengguna self-service")
    parser.add_argument("--out", type=Path, default=None, help="folder induk hasil (default: build/)")
    args = parser.parse_args(argv)
    if args.starter:
        print(f"Starter kit siap: {build_starter(ROOT, args.out)}")
        return 0
    if not args.kode:
        parser.error("isi kode instance atau pakai --starter")
    try:
        report = build(args.kode, ROOT, args.out)
    except ConfigError as error:
        print(f"GAGAL: {error}", file=sys.stderr)
        return 1
    print(f"Paket siap: {report['package']}")
    if report["unfilled"]:
        print(f"PERINGATAN: nilai belum diisi di tesis.yaml: {', '.join(report['unfilled'])}")
    if report["unresolved"]:
        print("PERINGATAN: placeholder tanpa nilai:\n  " + "\n  ".join(report["unresolved"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
