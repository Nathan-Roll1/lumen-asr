fn main() {
    let folder = std::env::args().nth(1).expect("model directory");
    let ready = lumen_models::qwen_ready(std::path::Path::new(&folder));
    println!("{}", ready);
}
