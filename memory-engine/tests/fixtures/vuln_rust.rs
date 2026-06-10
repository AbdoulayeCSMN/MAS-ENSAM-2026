// Test fixture — fichier Rust volontairement unsafe
// Cible : MEM-070 unsafe{}, MEM-071 transmute, MEM-073 Box::from_raw

use std::mem;

/* MEM-070 : bloc unsafe avec déréférencement pointeur brut */
fn raw_ptr_access(ptr: *mut i32) -> i32 {
    unsafe {                          // VULN: unsafe block
        *ptr = 42;
        *ptr
    }
}

/* MEM-071 : transmute — type safety bypass */
fn reinterpret(val: u64) -> f64 {
    unsafe {
        mem::transmute::<u64, f64>(val)  // VULN: transmute
    }
}

/* MEM-073 : Box::from_raw — double-free risk */
fn dangerous_box(raw: *mut String) -> Box<String> {
    unsafe {
        Box::from_raw(raw)            // VULN: ownership non garanti
    }
}

/* MEM-072 : ptr::read */
fn read_raw(ptr: *const u8) -> u8 {
    unsafe {
        std::ptr::read(ptr)           // VULN: ptr::read
    }
}

fn main() {
    let mut x = 0i32;
    let _ = raw_ptr_access(&mut x as *mut i32);
}
