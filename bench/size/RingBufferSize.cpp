#include <cstdint>
#include <cstdio>

#include "spsc/RingBuffer.h"
#include "mpsc/RingBuffer.h"
#include "spmc/RingBuffer.h"

namespace
{

    struct Payload64
    {
        uint8_t m_bytes[64];
    };

    template <typename T>
    static void print_sizeof(const char *name)
    {
        std::printf("%s sizeof=%zu\n", name, sizeof(T));
    }

} // namespace

int main()
{
    // ── SPSC ─────────────────────────────────────────────────────────────
    {
        using namespace ouroboros::spsc;

        print_sizeof<RingBuffer<uint8_t, 1024>>("spsc::RingBuffer<uint8_t,1024>");
        print_sizeof<RingBuffer<uint64_t, 65536>>("spsc::RingBuffer<uint64_t,65536>");
        print_sizeof<RingBuffer<Payload64, 4096>>("spsc::RingBuffer<Payload64,4096>");

        print_sizeof<ByteRingBuffer<65536>>("spsc::ByteRingBuffer<65536>");
    }

    // ── MPSC ─────────────────────────────────────────────────────────────
    {
        using namespace ouroboros::mpsc;

        print_sizeof<RingBuffer<uint64_t, 1024>>("mpsc::RingBuffer<uint64_t,1024>");
        print_sizeof<RingBuffer<Payload64, 256>>("mpsc::RingBuffer<Payload64,256>");
    }

    // ── SPMC ─────────────────────────────────────────────────────────────
    {
        using namespace ouroboros::spmc;

        print_sizeof<RingBuffer<uint64_t, 1024>>("spmc::RingBuffer<uint64_t,1024>");
        print_sizeof<RingBuffer<Payload64, 256>>("spmc::RingBuffer<Payload64,256>");
    }

    return 0;
}