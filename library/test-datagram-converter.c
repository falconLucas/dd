#include "datagram-converter.h"
#include <cbor.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

// static char list_keys[4][4];

static int test_datagram_converter_init(void)
{
    return 0;
}

void
print_buffer(uint8_t *buffer, size_t buffer_size)
{
    printf("Buffer @0x%lx, %ld bytes", (uint64_t)buffer, buffer_size);
    for(int i = 0; i < buffer_size; i++) {
        if(i % 16 == 0) printf("\n");
        printf("%02x ", buffer[i]);
    }
    printf("\n\n");
}

int test_datagram_converter(void)
{
    uint8_t buffer[256];
    dd_datagram_t datagram;
    dd_object_t root;
    dd_object_t child[2];
    dd_object_t cchild[2];
    dd_object_t cchild2[2];
    dd_object_t list_elements[5];

    datagram.root = &root;

    root.data = NULL;
    root.type = DD_TYPE_DICT;
    root.key = "root";
    root.data_length = 2;
    root.child = child;

    child[0].type = DD_TYPE_DICT;
    child[0].data = NULL;
    child[0].key = "child1";
    child[0].data_length = 2;
    child[0].child = cchild;

    long data = 1234;
    cchild[0].type = DD_TYPE_INTEGER;
    cchild[0].data = &data;
    cchild[0].key = "cchild1";
    cchild[0].data_length = 0;
    cchild[0].child = NULL;

    cchild[1].type = DD_TYPE_STRING;
    cchild[1].data = "Hello World!";
    cchild[1].key = "cchild2";
    cchild[1].data_length = 0;
    cchild[1].child = NULL;

    child[1].type = DD_TYPE_DICT;
    child[1].data = NULL;
    child[1].key = "child2";
    child[1].data_length = 2;
    child[1].child = cchild2;

    double pi = 3.141592653589793238462643383279502884197169399375105820974944592307816406286;
    cchild2[0].type = DD_TYPE_FLOAT;
    cchild2[0].data = &pi;
    cchild2[0].key = "cchild1";
    cchild2[0].data_length = 0;
    cchild2[0].child = NULL;

    cchild2[1].type = DD_TYPE_LIST;
    cchild2[1].data = NULL;
    cchild2[1].key = "cchild2";
    cchild2[1].data_length = 5;
    cchild2[1].child = list_elements;

    list_elements[0].type = DD_TYPE_INTEGER;
    list_elements[0].data = &data;
    list_elements[0].key = "[0]";//list_keys[0];
    list_elements[0].data_length = 0;
    list_elements[0].child = NULL;

    list_elements[1].type = DD_TYPE_FLOAT;
    list_elements[1].data = &pi;
    list_elements[1].key = "[1]";//list_keys[1];
    list_elements[1].data_length = 0;
    list_elements[1].child = NULL;

    list_elements[2].type = DD_TYPE_STRING;
    list_elements[2].data = "Hello DD!";
    list_elements[2].key = "[2]";//list_keys[2];
    list_elements[2].data_length = 0;
    list_elements[2].child = NULL;
    
    list_elements[3].type = DD_TYPE_DICT;
    list_elements[3].data = NULL;
    list_elements[3].key = "[3]";//list_keys[3];
    list_elements[3].data_length = 2;
    list_elements[3].child = cchild;

    list_elements[4].type = DD_TYPE_LIST;
    list_elements[4].data = NULL;
    list_elements[4].key = "[4]";//list_keys[4];
    list_elements[4].data_length = 1;
    list_elements[4].child = list_elements;

    size_t cbor_size = 0;
    if(datagram_converter_encode_datagram(&datagram, buffer, sizeof(buffer), &cbor_size) != 0) {
        return -1;
    }
    print_buffer(buffer, cbor_size);

    if(datagram_converter_decode_datagram(&datagram, buffer, sizeof(buffer)) != 0) {
        return -2;
    }
    uint8_t buffer2[256];
    if(datagram_converter_encode_datagram(&datagram, buffer2, sizeof(buffer2), &cbor_size) != 0) {
        return -3;
    }
    print_buffer(buffer2, cbor_size);
    int ret = memcmp(buffer, buffer2, cbor_size);
    if(ret != 0) {
        printf("Buffers are not equal!\n");
        return -4;
    }
    return 0;
}

int main(void)
{
    assert(test_datagram_converter_init() == 0);
    assert(test_datagram_converter() == 0);
    printf("\nAll tests passed!\n");
    return 0;
}