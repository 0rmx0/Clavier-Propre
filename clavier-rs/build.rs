fn main() {
    slint_build::compile_with_config(
        "ui/app.slint",
        slint_build::CompilerConfiguration::default()
            .with_style("fluent".into()),
    )
    .expect("Slint UI compilation failed");

    // Embarque l'icône dans l'exécutable Windows via le fichier de ressources.
    // Sur les cibles Windows (MSVC et MinGW) embed_resource compile le .rc
    // avec rc.exe/windres. Sur les autres cibles, c'est un no-op.
    println!("cargo:rerun-if-changed=clavier.ico");
    println!("cargo:rerun-if-changed=clavier.rc");
    let _ = embed_resource::compile("clavier.rc", embed_resource::NONE);
}
