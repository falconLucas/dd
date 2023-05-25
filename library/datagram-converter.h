#ifndef DATAGRAM_CONVERTER_H
#define DATAGRAM_CONVERTER_H

#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

typedef enum {
    DD_TYPE_DICT,
    DD_TYPE_FLOAT,
    DD_TYPE_INTEGER,
    DD_TYPE_LIST,
    DD_TYPE_STRING
} dd_type_t;

typedef struct dd_object dd_object_t;
typedef struct dd_object {
    dd_object_t *child;
    void *data;
    dd_type_t type;
    char *key;
    size_t data_length;
} dd_object_t;

typedef struct {
    const dd_object_t *root;
} dd_datagram_t;

int datagram_converter_init(void);
int datagram_converter_encode_datagram(dd_datagram_t *in_datagram, uint8_t *out_buffer, size_t buffer_size, size_t *buffer_size_used);
int datagram_converter_decode_datagram(dd_datagram_t *out_datagram, uint8_t *in_buffer, size_t buffer_size);


#endif // DATAGRAM_CONVERTER_H