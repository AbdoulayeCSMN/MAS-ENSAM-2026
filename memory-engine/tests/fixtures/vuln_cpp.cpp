/*
 * Test fixture — fichier C++ volontairement vulnérable
 * Cible : MEM-021 new sans delete, MEM-080 delete[], MEM-081 memcpy
*/

#include <cstring>
#include <iostream>

/* MEM-021 : new sans delete (memory leak) */
void create_object() {
    int *arr = new int[100];   /* VULN: jamais libéré */
    arr[0] = 42;
}

/* MEM-080 : delete[] mismatch */
void bad_delete() {
    int *p = new int(5);
    delete[] p;               /* VULN: new int → delete[], pas delete */
}

/* MEM-081 : memcpy avec buffers potentiellement chevauchants */
void copy_buffers(char *src, int n) {
    char *dst = src + 10;
    memcpy(dst, src, n);      /* VULN: possible overlap */
}

/* MEM-001 via C++ */
void unsafe_copy(const char *input) {
    char local[64];
    strcpy(local, input);     /* VULN: buffer overflow */
}

int main() {
    create_object();
    return 0;
}
