#include "datagram-converter.h"
#include "dd-protocol.h"
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

int test_generated_code(void)
{
    uint8_t buffer[2048];
    size_t buffer_size_used = 0;
    if(dd_encode(&buffer[0], sizeof(buffer), &buffer_size_used) != 0) {
        return -1;
    }
    print_buffer(buffer, buffer_size_used);
    if(dd_decode(&buffer[0], sizeof(buffer)) != 0) {
        return -2;
    }
    return 0;
}

int main(void)
{
    assert(test_datagram_converter_init() == 0);
    assert(test_generated_code() == 0);
    printf("\nAll tests passed!\n");
    return 0;
}