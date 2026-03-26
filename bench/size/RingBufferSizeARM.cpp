// ─────────────────────────────────────────────────────────────────────────────
// RingBufferSizeARM.cpp — Freestanding ARM code-size measurement harness
//
// Compiled with -c only (no linking). Depends on <cstring> (std::memcpy)
// from the toolchain's C library (newlib for arm-none-eabi).
//
//   arm-none-eabi-g++ -std=c++17 -Os -mcpu=cortex-m4 -mthumb -ffreestanding \
//       -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections \
//       -I inc -c bench/size/RingBufferSizeARM.cpp -o arm_m4.o
// ─────────────────────────────────────────────────────────────────────────────

#include "spsc/RingBuffer.h"
#include "mpsc/RingBuffer.h"
#include "spmc/RingBuffer.h"

namespace
{

volatile bool     g_boolSink __attribute__((used));
volatile uint8_t  g_u8Sink   __attribute__((used));
volatile uint64_t g_u64Sink  __attribute__((used));
volatile uint32_t g_u32Sink  __attribute__((used));

// ─────────────────────────────────────────────────────────────────────────────
// SPSC — uint8_t, capacity 256 — exercises full API including bulk ops
// ─────────────────────────────────────────────────────────────────────────────

__attribute__((used))
void spsc_uint8_ops()
{
    ouroboros::spsc::RingBuffer<uint8_t, 256> rb;

    uint8_t val = 0xAB;
    g_boolSink = rb.push(val);

    uint8_t out{};
    g_boolSink = rb.pop(out);
    g_u8Sink   = out;

    uint8_t bulk[8] = {1, 2, 3, 4, 5, 6, 7, 8};
    g_boolSink = rb.write(bulk, 8);

    uint8_t dst[8]{};
    g_boolSink = rb.peek(dst, 4);
    g_u8Sink   = dst[0];

    g_boolSink = rb.read(dst, 8);
    g_u8Sink   = dst[7];

    g_boolSink = rb.skip(2);

    g_u32Sink  = rb.readAvailable();
    g_u32Sink  = rb.writeAvailable();
    g_boolSink = rb.isEmpty();
    g_boolSink = rb.isFull();

    rb.reset();
}

// ─────────────────────────────────────────────────────────────────────────────
// SPSC — uint64_t, capacity 1024
// ─────────────────────────────────────────────────────────────────────────────

__attribute__((used))
void spsc_u64_ops()
{
    ouroboros::spsc::RingBuffer<uint64_t, 64> rb;

    uint64_t val = 0xDEADBEEF;
    g_boolSink = rb.push(val);

    uint64_t out{};
    g_boolSink = rb.pop(out);
    g_u64Sink  = out;

    uint64_t bulk[4] = {1, 2, 3, 4};
    g_boolSink = rb.write(bulk, 4);

    uint64_t dst[4]{};
    g_boolSink = rb.read(dst, 4);
    g_u64Sink  = dst[0];
}

// ─────────────────────────────────────────────────────────────────────────────
// MPSC — uint64_t, capacity 256
// ─────────────────────────────────────────────────────────────────────────────

__attribute__((used))
void mpsc_u64_ops()
{
    ouroboros::mpsc::RingBuffer<uint64_t, 256> rb;

    uint64_t val = 0xCAFEBABE;
    g_boolSink = rb.push(val);

    uint64_t out{};
    g_boolSink = rb.pop(out);
    g_u64Sink  = out;

    g_u32Sink  = rb.readAvailable();
    g_u32Sink  = rb.writeAvailable();
    g_boolSink = rb.isEmpty();
    g_boolSink = rb.isFull();

    rb.reset();
}

// ─────────────────────────────────────────────────────────────────────────────
// SPMC — uint64_t, capacity 256
// ─────────────────────────────────────────────────────────────────────────────

__attribute__((used))
void spmc_u64_ops()
{
    ouroboros::spmc::RingBuffer<uint64_t, 256> rb;

    uint64_t val = 0xBAADF00D;
    g_boolSink = rb.push(val);

    uint64_t out{};
    g_boolSink = rb.pop(out);
    g_u64Sink  = out;

    g_u32Sink  = rb.readAvailable();
    g_u32Sink  = rb.writeAvailable();
    g_boolSink = rb.isEmpty();
    g_boolSink = rb.isFull();

    rb.reset();
}

} // namespace
