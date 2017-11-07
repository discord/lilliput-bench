import time
from cStringIO import StringIO
from PIL import Image, ImageOps

def analyze_gif(blob):
    im = Image.open(blob)
    results = {
        'size': im.size,
        'mode': 'full',
    }
    try:
        while True:
            if im.tile:
                tile = im.tile[0]
                update_region = tile[1]
                update_region_dimensions = update_region[2:]
                if update_region_dimensions != im.size:
                    results['mode'] = 'partial'
                    break
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return results


def resize_gif(blob, width, height, write_to=''):
    mode = analyze_gif(blob)['mode']
    im = Image.open(blob)

    i = 0
    p = im.getpalette()
    last_frame = ImageOps.fit(im.convert('RGBA'), (width, height), Image.LANCZOS)
    frames = []

    try:
        while True:
            if not im.getpalette():
                im.putpalette(p)

            new_frame = Image.new('RGBA', (width, height))

            if mode == 'partial':
                new_frame.paste(last_frame)

            resized_frame = ImageOps.fit(im, (width, height), Image.LANCZOS)
            new_frame.paste(resized_frame, (0,0), resized_frame.convert('RGBA'))

            i += 1
            last_frame = new_frame
            frames.append(new_frame)
            im.seek(im.tell() + 1)
    except EOFError:
        pass

    output = StringIO()
    first_frame = frames[0]
    first_frame.save(output, 'GIF', save_all=True, append_images=frames[1:])
    size = len(output.getvalue())
    if write_to:
        with open(write_to, 'wb') as f:
            f.write(output.getvalue())
    output.close()
    return size


def bench_header(path, num_iter):
    with open(path) as f:
        blob = f.read()
    blob = StringIO(blob)
    timings = []
    for i in xrange(num_iter):
        start = time.time()
        im = Image.open(blob)
        width, height = im.size
        if i == 0:
            print '%dx%d,' % (width, height),
        stop = time.time()
        timings.append(stop - start)
    timings.sort()
    print 'avg: %.6f ms' % (sum(timings)/len(timings) * 1000),
    print 'min: %.6f ms' % (timings[0] * 1000),
    print 'max: %.6f ms' % (timings[-1] * 1000)


save_opts = {
    'JPEG': {
        'quality': 85,
    },
    'PNG': {
        'compress_level': 7,
    },
    'WEBP': {
        'quality': 85,
    },
    'GIF': {},
}


def bench_resize(path, output_type, width, height, num_iter):
    with open(path) as f:
        blob = f.read()
    blob = StringIO(blob)
    timings = []
    for i in xrange(num_iter):
        start = time.time()
        im = Image.open(blob)
        im = im.convert('RGB' if output_type == 'JPEG' else 'RGBA')
        im = ImageOps.fit(im, (width, height), Image.LANCZOS)
        output = StringIO()
        im.save(output, output_type, **save_opts[output_type])
        if i == 0:
            print '%d Bytes,' % len(output.getvalue()),
            with open('py_%d.%s' % (width, output_type.lower()), 'wb') as f:
                f.write(output.getvalue())
        output.close()
        stop = time.time()
        timings.append(stop - start)
    timings.sort()
    print 'avg: %.2f ms' % (sum(timings)/len(timings) * 1000),
    print 'min: %.2f ms' % (timings[0] * 1000),
    print 'max: %.2f ms' % (timings[-1] * 1000)


def bench_resize_gif(path, width, height, num_iter):
    with open(path) as f:
        blob = f.read()
    blob = StringIO(blob)
    timings = []
    for i in xrange(num_iter):
        start = time.time()
        path = '' if i != 0 else 'py_%d.gif' % width
        size = resize_gif(blob, width, height, path)
        if i == 0:
            print '%d Bytes,' % size,
        stop = time.time()
        timings.append(stop - start)
    timings.sort()
    print 'avg: %.2f ms' % (sum(timings)/len(timings) * 1000),
    print 'min: %.2f ms' % (timings[0] * 1000),
    print 'max: %.2f ms' % (timings[-1] * 1000)


def bench_transcode(path, output_type, num_iter):
    with open(path) as f:
        blob = f.read()
    blob = StringIO(blob)
    timings = []
    for i in xrange(num_iter):
        start = time.time()
        im = Image.open(blob)
        output = StringIO()
        im.save(output, output_type, **save_opts[output_type])
        if i == 0:
            print '%d Bytes,' % len(output.getvalue()),
            with open('py_%s_transcode.%s' % (path, output_type.lower()), 'wb') as f:
                f.write(output.getvalue())
        output.close()
        stop = time.time()
        timings.append(stop - start)
    timings.sort()
    print 'avg: %.2f ms' % (sum(timings)/len(timings) * 1000),
    print 'min: %.2f ms' % (timings[0] * 1000),
    print 'max: %.2f ms' % (timings[-1] * 1000)


def main():
    print 'JPEG 1920x1080 header read:',
    bench_header('1920.jpeg', 10000)
    print 'PNG 1920x1080 header read:',
    bench_header('1920.png', 10000)
    print 'WEBP 1920x1080 header read:',
    bench_header('1920.webp', 100)
    print 'GIF 1920x1080 header read:',
    bench_header('1920.gif', 10000)

    print 'JPEG 256x256 => 32x32:',
    bench_resize('256.jpeg', 'JPEG', 32, 32, 1000)
    print 'PNG 256x256 => 32x32:',
    bench_resize('256.png', 'PNG', 32, 32, 1000)
    print 'WEBP 256x256 => 32x32:',
    bench_resize('256.webp', 'WEBP', 32, 32, 1000)
    print 'GIF 256x256 => 32x32:',
    bench_resize_gif('256.gif', 32, 32, 1000)

    print 'JPEG 1920x1080 => 800x600:',
    bench_resize('1920.jpeg', 'JPEG', 800, 600, 100)
    print 'PNG 1920x1080 => 800x600:',
    bench_resize('1920.png', 'PNG', 800, 600, 100)
    print 'WEBP 1920x1080 => 800x600:',
    bench_resize('1920.webp', 'WEBP', 800, 600, 100)
    print 'GIF 1920x1080 => 800x600:',
    bench_resize_gif('1920.gif', 800, 600, 50)

    print 'PNG 256x256 => WEBP 256x256:',
    bench_transcode('256.png', 'WEBP', 100)
    print 'JPEG 256x256 => PNG 256x256:',
    bench_transcode('256.jpeg', 'PNG', 100)
    print 'GIF 256x256 => PNG 256x256:',
    bench_transcode('256.gif', 'PNG', 100)

if __name__ == '__main__':
    main()
