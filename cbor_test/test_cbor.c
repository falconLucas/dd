#include <cbor.h>
#include <stdio.h>

int main(void) {
  /* Preallocate the map structure */
  cbor_item_t* root = cbor_new_definite_map(2);
  /* Add the content */
  bool success = cbor_map_add(
      root, (struct cbor_pair){
                .key = cbor_move(cbor_build_string("Is CBOR awesome?")),
                .value = cbor_move(cbor_build_bool(true))});
  success &= cbor_map_add(
      root, (struct cbor_pair){
                .key = cbor_move(cbor_build_uint8(42)),
                .value = cbor_move(cbor_build_string("Is the answer"))});
  if (!success) return 1;
  /* Output: `length` bytes of data in the `buffer` */
  unsigned char* buffer;
  size_t buffer_size;
  cbor_serialize_alloc(root, &buffer, &buffer_size);

  // fwrite(buffer, 1, buffer_size, stdout);

  for(int i = 0; i < buffer_size; i++) {
    if(buffer[i] < 0x7E && buffer[i] >= 0x20) {
      printf("%c ", buffer[i]);
    } else {
      printf("0x%02x ", buffer[i]);
    }
  }
  printf("\n");
  free(buffer);


  fflush(stdout);
  cbor_decref(&root);
}