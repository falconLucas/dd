
TARGET_EXEC ?= test-datagram-converter

BUILD_DIR ?= build
												
SRCS := test-datagram-converter.c datagram-converter.c
OBJS := $(SRCS:%=$(BUILD_DIR)/%.o)
DEPS := $(OBJS:.o=.d)

SRC_DIRS := . ../output
INC_DIRS := $(SRC_DIRS)
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


test: $(BUILD_DIR)/$(TARGET_EXEC)
	./$(BUILD_DIR)/$(TARGET_EXEC)

test-generated-code: test
	$(CC) $(CPPFLAGS) $(CFLAGS) ../output/dd-protocol.c $(DEP_FLAGS) -o $(BUILD_DIR)/dd-protocol.o $(LDFLAGS)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c test-generated-code.c $(DEP_FLAGS) -o $(BUILD_DIR)/test-generated-code
	./$(BUILD_DIR)/test-generated-code

.PHONY: clean

clean:
	$(RM) -r $(BUILD_DIR)

-include $(DEPS)