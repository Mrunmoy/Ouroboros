#include <mpsc/RingBuffer.h>

#include <cstddef>
#include <cstdint>

// ── Helpers ─────────────────────────────────────────────────────────

static constexpr uint32_t kCapacity = 64;
using Ring = ouroboros::mpsc::RingBuffer<uint8_t, kCapacity>;

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
        switch (op & 0x07) {

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

        case 2: { // reset
            g_ring.reset();
            break;
        }

        case 3: { // readAvailable / writeAvailable queries
            (void)g_ring.readAvailable();
            (void)g_ring.writeAvailable();
            break;
        }

        case 4: { // isEmpty / isFull queries
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
