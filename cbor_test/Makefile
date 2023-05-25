
TARGET_EXEC ?= test_cbor

BUILD_DIR ?= build
												
SRCS := test_cbor.c
OBJS := $(SRCS:%=$(BUILD_DIR)/%.o)
DEPS := $(OBJS:.o=.d)

INC_DIRS := .
INC_FLAGS := $(addprefix -I,$(INC_DIRS))
DEP_FLAGS := -lcbor
			

CPPFLAGS ?= $(INC_FLAGS) -MMD -MP 
CFLAGS += -lcbor -Wall -Werror -Wno-stringop-truncation -g -std=gnu11 -O2

$(BUILD_DIR)/$(TARGET_EXEC): $(OBJS)
	$(CC) $(OBJS) $(DEP_FLAGS) -o $@ $(LDFLAGS)

# c source
$(BUILD_DIR)/%.c.o: %.c
	mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< $(DEP_FLAGS) -o $@

.PHONY: clean

clean:
	$(RM) -r $(BUILD_DIR)

-include $(DEPS)