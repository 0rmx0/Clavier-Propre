fn main() {
    slint_build::compile_with_config(
        "ui/app.slint",
        slint_build::CompilerConfiguration::default()
            .with_style("fluent".into()),
    )
    .expect("Slint UI compilation failed");
}
