
#include "datagram-converter.h"
#include <cbor.h>
#include <stdio.h>
#include <string.h>

#define RECURSION_DEPTH_LIMIT 10

int datagram_converter_init(void)
{
    return 0;
}

static int
encode_datagram_recursive(cbor_item_t *out_cbor, const dd_object_t *in_object, uint8_t *out_buffer, size_t buffer_size, size_t depth)
{
    if(depth > RECURSION_DEPTH_LIMIT) {
        return -1;
    }
    cbor_item_t *key = cbor_build_string(in_object->key);
    cbor_item_t *value = NULL;
    int ret = 0;
    switch(in_object->type) {
        case DD_TYPE_DICT:
            value = cbor_new_definite_map(in_object->data_length);
            for(int i = 0; i < in_object->data_length; i++) {
                ret = encode_datagram_recursive(value, in_object->child + i, out_buffer, buffer_size, depth + 1);
                if(ret != 0) break;
            }
            break;
        case DD_TYPE_LIST:
            value = cbor_new_definite_array(in_object->data_length);
            for(int i = 0; i < in_object->data_length; i++) {
                cbor_item_t *element = cbor_new_definite_map(1);
                ret = encode_datagram_recursive(element, in_object->child + i, out_buffer, buffer_size, depth + 1);
                cbor_array_set(value, i, cbor_map_handle(element)->value);
                if(ret != 0) break;
            }
            break;
        case DD_TYPE_FLOAT:
            value = cbor_build_float8(*(double *)in_object->data);
            break;
        case DD_TYPE_INTEGER:
            value = cbor_build_uint64(*(uint64_t *)in_object->data);
            break;
        case DD_TYPE_STRING:
            value = cbor_build_string((char *)in_object->data);
            break;
        default:
            ret = -1;
            break;
    }
    if (ret != 0) {
        return ret;
    }
    return cbor_map_add(out_cbor, (struct cbor_pair){
        .key = cbor_move(key),
        .value = cbor_move(value)
    }) ? 0 : -1;
}

static int
decode_datagram_recursive(const dd_object_t *out_object, cbor_item_t *in_item, uint8_t *in_buffer, size_t buffer_size, size_t depth)
{
    if(depth > RECURSION_DEPTH_LIMIT) {
        return -1;
    }
    struct cbor_pair *pair = cbor_map_handle(in_item);
    if(memcmp(out_object->key, pair->key->data, strlen(out_object->key)) != 0) {
        return -1;
    }
    int ret = 0;
    switch(cbor_typeof(in_item)) {
        case CBOR_TYPE_MAP:
            if(out_object->type != DD_TYPE_DICT) {
                ret = -1;
                break;
            }
            // if(out_object->data_length != cbor_map_size(in_item)) {
            //     ret = -1;
            //     break;
            // }
            for(int i = 0; i < out_object->data_length; i++) {
                decode_datagram_recursive(out_object->child + i, cbor_map_handle(in_item)->value, in_buffer, buffer_size, depth + 1);
            }
            break;
        case CBOR_TYPE_FLOAT_CTRL:
            if(out_object->type != DD_TYPE_FLOAT) {
                ret = -1;
                break;
            }
            *(double *)out_object->data = cbor_float_get_float8(in_item);
            break;
        case CBOR_TYPE_UINT:
        case CBOR_TYPE_NEGINT:
            if(out_object->type != DD_TYPE_INTEGER) {
                ret = -1;
                break;
            }
            *(uint64_t *)out_object->data = cbor_get_uint64(in_item);
            break;
        case CBOR_TYPE_STRING:
            if(out_object->type != DD_TYPE_STRING) {
                ret = -1;
                break;
            }
            if(out_object->data_length < cbor_string_length(in_item)) {
                ret = -1;
                break;
            }
            memcpy(out_object->data, cbor_string_handle(in_item), out_object->data_length);
            break;
        case CBOR_TYPE_ARRAY:
            if(out_object->type != DD_TYPE_LIST) {
                ret = -1;
                break;
            }
            if(out_object->data_length != cbor_array_size(in_item)) {
                ret = -1;
                break;
            }
            for(int i = 0; i < out_object->data_length; i++) {
                decode_datagram_recursive(out_object->child + i, cbor_array_get(in_item, i), in_buffer, buffer_size, depth + 1);
            }
            break;
        default:
            ret = -1;
            break;
    }
    return ret;
}

int
datagram_converter_encode_datagram(dd_datagram_t *in_datagram, uint8_t *out_buffer, size_t buffer_size, size_t *buffer_size_used)
{
    cbor_item_t *root = cbor_new_indefinite_map();
    size_t l_buf_size_used = 0;
    if(encode_datagram_recursive(root, in_datagram->root, out_buffer, buffer_size, 0) == 0) {
        l_buf_size_used = cbor_serialize(root, out_buffer, buffer_size);
    } else {
        return -1;
    }

    /* Fill the unused part of the buffer with DD */
    for(size_t i = l_buf_size_used; i < buffer_size; i++) {
        out_buffer[i] = 0xDD;
    }

    if(buffer_size_used != NULL) {
        *buffer_size_used = l_buf_size_used;
    }
    return l_buf_size_used > 0 ? 0 : -1;
}

int
datagram_converter_decode_datagram(dd_datagram_t *out_datagram, uint8_t *in_buffer, size_t buffer_size)
{
    struct cbor_load_result result;
    cbor_item_t *root = cbor_load((unsigned char *)in_buffer, buffer_size, &result);
    if(result.error.code != CBOR_ERR_NONE) {
        printf("CBOR error: %d\n", result.error.code);
        return -1;
    }
    return decode_datagram_recursive(out_datagram->root, root, in_buffer, buffer_size, 0);
}
