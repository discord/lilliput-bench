package main

import (
	"fmt"
	"io/ioutil"
	"sort"
	"time"

	"github.com/discordapp/lilliput"
)

var Ops *lilliput.ImageOps

var EncodeOptions = map[string]map[int]int{
	".jpeg": map[int]int{lilliput.JpegQuality: 85},
	".png":  map[int]int{lilliput.PngCompression: 7},
	".webp": map[int]int{lilliput.WebpQuality: 85},
}

type durations []time.Duration

func (d durations) Len() int           { return len(d) }
func (d durations) Less(a, b int) bool { return d[a] < d[b] }
func (d durations) Swap(a, b int)      { d[a], d[b] = d[b], d[a] }

func bench_header(path string, numIter int) {
	inputBuf, _ := ioutil.ReadFile(path)

	timings := make(durations, 0)
	for i := 0; i < numIter; i++ {
		start := time.Now()
		decoder, _ := lilliput.NewDecoder(inputBuf)
		header, _ := decoder.Header()
		if i == 0 {
			fmt.Printf("%dx%d, ", header.Width(), header.Height())
		}
		decoder.Close()
		timings = append(timings, time.Since(start))
	}

	sort.Sort(timings)

	totalTime := time.Duration(0)
	for _, t := range timings {
		totalTime += t
	}

	fmt.Printf("avg: %.6f ms, ", totalTime.Seconds()/float64(len(timings))*1000)
	fmt.Printf("min: %.6f ms, ", timings[0].Seconds()*1000)
	fmt.Printf("max: %.6f ms", timings[len(timings)-1].Seconds()*1000)
	fmt.Printf("\n")
}

func bench_resize(path string, outputType string, width, height, numIter int) {
	inputBuf, _ := ioutil.ReadFile(path)

	outputImg := make([]byte, 50*1024*1024)
	opts := &lilliput.ImageOptions{
		FileType:      outputType,
		Width:         width,
		Height:        height,
		ResizeMethod:  lilliput.ImageOpsFit,
		EncodeOptions: EncodeOptions[outputType],
	}

	timings := make(durations, 0)
	for i := 0; i < numIter; i++ {
		start := time.Now()
		decoder, _ := lilliput.NewDecoder(inputBuf)
		outputImg, _ = Ops.Transform(decoder, opts, outputImg)
		if i == 0 {
			fmt.Printf("%d Bytes, ", len(outputImg))
			ioutil.WriteFile(fmt.Sprintf("go_%d%s", width, outputType), outputImg, 0400)
		}
		decoder.Close()
		timings = append(timings, time.Since(start))
	}

	sort.Sort(timings)

	totalTime := time.Duration(0)
	for _, t := range timings {
		totalTime += t
	}

	fmt.Printf("avg: %.2f ms, ", totalTime.Seconds()/float64(len(timings))*1000)
	fmt.Printf("min: %.2f ms, ", timings[0].Seconds()*1000)
	fmt.Printf("max: %.2f ms", timings[len(timings)-1].Seconds()*1000)
	fmt.Printf("\n")
}

func bench_transcode(path string, outputType string, numIter int) {
	inputBuf, _ := ioutil.ReadFile(path)

	outputImg := make([]byte, 50*1024*1024)
	opts := &lilliput.ImageOptions{
		FileType:      outputType,
		ResizeMethod:  lilliput.ImageOpsNoResize,
		EncodeOptions: EncodeOptions[outputType],
	}

	timings := make(durations, 0)
	for i := 0; i < numIter; i++ {
		start := time.Now()
		decoder, _ := lilliput.NewDecoder(inputBuf)
		outputImg, _ = Ops.Transform(decoder, opts, outputImg)
		if i == 0 {
			fmt.Printf("%d Bytes, ", len(outputImg))
			ioutil.WriteFile(fmt.Sprintf("go_%s_transcode%s", path, outputType), outputImg, 0400)
		}
		decoder.Close()
		timings = append(timings, time.Since(start))
	}

	sort.Sort(timings)

	totalTime := time.Duration(0)
	for _, t := range timings {
		totalTime += t
	}

	fmt.Printf("avg: %.2f ms, ", totalTime.Seconds()/float64(len(timings))*1000)
	fmt.Printf("min: %.2f ms, ", timings[0].Seconds()*1000)
	fmt.Printf("max: %.2f ms", timings[len(timings)-1].Seconds()*1000)
	fmt.Printf("\n")
}

func main() {
	Ops = lilliput.NewImageOps(8192)
	defer Ops.Close()

	fmt.Printf("JPEG 1920x1080 header read: ")
	bench_header("1920.jpeg", 100000)

	fmt.Printf("PNG 1920x1080 header read: ")
	bench_header("1920.png", 100000)

	fmt.Printf("WEBP 1920x1080 header read: ")
	bench_header("1920.webp", 100000)

	fmt.Printf("GIF 1920x1080 header read: ")
	bench_header("1920.gif", 100000)

	fmt.Printf("JPEG 256x256 => 32x32: ")
	bench_resize("256.jpeg", ".jpeg", 32, 32, 1000)

	fmt.Printf("PNG 256x256 => 32x32: ")
	bench_resize("256.png", ".png", 32, 32, 1000)

	fmt.Printf("WEBP 256x256 => 32x32: ")
	bench_resize("256.webp", ".webp", 32, 32, 1000)

	fmt.Printf("GIF 256x256 => 32x32: ")
	bench_resize("256.gif", ".gif", 32, 32, 1000)

	fmt.Printf("JPEG 1920x1080 => 800x600: ")
	bench_resize("1920.jpeg", ".jpeg", 800, 600, 100)

	fmt.Printf("PNG 1920x1080 => 800x600: ")
	bench_resize("1920.png", ".png", 800, 600, 100)

	fmt.Printf("WEBP 1920x1080 => 800x600: ")
	bench_resize("1920.webp", ".webp", 800, 600, 100)

	fmt.Printf("GIF 1920x1080 => 800x600: ")
	bench_resize("1920.gif", ".gif", 800, 600, 50)

	fmt.Printf("PNG 256x256 => WEBP 256x256: ")
	bench_transcode("256.png", ".webp", 1000)

	fmt.Printf("JPEG 256x256 => PNG 256x256: ")
	bench_transcode("256.jpeg", ".png", 1000)

	fmt.Printf("GIF 256x256 => PNG 256x256: ")
	bench_transcode("256.gif", ".png", 1000)
}
