#include <spsc/RingBuffer.h>

#include <cstddef>
#include <cstdint>
#include <cstring>

// ── Helpers ─────────────────────────────────────────────────────────

static constexpr uint32_t kCapacity = 256;
using Ring = ouroboros::spsc::RingBuffer<uint8_t, kCapacity>;

static Ring g_ring;

static void checkInvariants(const Ring &rb) {
    uint32_t r = rb.readAvailable();
    uint32_t w = rb.writeAvailable();
    if (r + w != kCapacity) __builtin_trap();
    if (rb.isEmpty() != (r == 0)) __builtin_trap();
    if (rb.isFull() != (w == 0)) __builtin_trap();
}

// ── Fuzz entry point ────────────────────────────────────────────────

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    g_ring.reset();

    size_t i = 0;
    while (i < size) {
        uint8_t op = data[i++];
        switch (op & 0x0F) {

        case 0: { // push
            if (i >= size) break;
            uint8_t val = data[i++];
            (void)g_ring.push(val);
            break;
        }

        case 1: { // pop
            uint8_t val;
            (void)g_ring.pop(val);
            break;
        }

        case 2: { // bulk write
            if (i >= size) break;
            uint8_t count = (data[i++] % 32) + 1;
            uint32_t avail = (size - i < count) ? static_cast<uint32_t>(size - i) : count;
            if (avail > 0)
                (void)g_ring.write(data + i, avail);
            i += avail;
            break;
        }

        case 3: { // bulk read
            if (i >= size) break;
            uint8_t count = (data[i++] % 32) + 1;
            uint8_t buf[32];
            (void)g_ring.read(buf, count);
            break;
        }

        case 4: { // peek
            if (i >= size) break;
            uint8_t count = (data[i++] % 32) + 1;
            uint8_t buf[32];
            (void)g_ring.peek(buf, count);
            break;
        }

        case 5: { // skip
            if (i >= size) break;
            uint8_t count = (data[i++] % 32) + 1;
            (void)g_ring.skip(count);
            break;
        }

        case 6: { // reset
            g_ring.reset();
            break;
        }

        case 7: { // readAvailable / writeAvailable queries
            (void)g_ring.readAvailable();
            (void)g_ring.writeAvailable();
            break;
        }

        case 8: { // isEmpty / isFull queries
            (void)g_ring.isEmpty();
            (void)g_ring.isFull();
            break;
        }

        default: { // push with op byte as value
            (void)g_ring.push(op);
            break;
        }
        }

        checkInvariants(g_ring);
    }

    return 0;
}
