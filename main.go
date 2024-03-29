package main

import (
	"bufio"
	"io"
	"log"
	"os"
	"os/exec"
	"time"

	"github.com/gofiber/fiber/v2"
)

func main() {
	app := fiber.New()

	app.Get("/", func(c *fiber.Ctx) error {
		return c.Render("index.html", fiber.Map{})
	})

	app.Post("/submit", func(c *fiber.Ctx) error {
		// Get the file from the form.
		file, err := c.FormFile("file")
		if err != nil {
			return err
		}

		// Get the text from the form.
		password := c.FormValue("text")

		// Save the file.
		if err := c.SaveFile(file, "./"+file.Filename); err != nil {
			return err
		}

		cmdStr := "python3"
		cmdArg := []string{}
		if os.Getenv("USE_PYTHON_BIN") == "True" {
			cmdStr = "/app/pdf-to-graph"
		} else {
			cmdArg = append(cmdArg, "main.py")
		}
		cmdArg = append(cmdArg, "-f")
		cmdArg = append(cmdArg, file.Filename)
		if password != "" {
			cmdArg = append(cmdArg, "-p")
			cmdArg = append(cmdArg, password)
		}
		cmdArg = append(cmdArg, "-g")
		cmdArg = append(cmdArg, "True")

		// Execute the Python script.
		cmd := exec.Command(cmdStr, cmdArg...)
		stdout, err := cmd.StdoutPipe()
		if err != nil {
			return err
		}
		_, err = cmd.StderrPipe()
		if err != nil {
			return err
		}
		err = cmd.Start()
		if err != nil {
			return err
		}

		stdoutStr := ""
		// stderrStr := ""

		go func() {
			stdoutStr = copyOutput(stdout)
		}()
		// go func() {
		// 	stderrStr = copyOutput(stderr)
		// }()
		cmd.Wait()

		if stdoutStr != "" {
			c.WriteString(stdoutStr)
			return nil
		}

		os.Remove(file.Filename)

		timer := time.NewTimer(5 * time.Second)
		go func() {
			<-timer.C
			os.Remove(file.Filename + ".html")
		}()

		// Send the HTML response.
		return c.Render(file.Filename+".html", fiber.Map{})
	})

	log.Fatal(app.Listen(":8082"))
}

func copyOutput(r io.Reader) string {
	res := ""
	scanner := bufio.NewScanner(r)
	for scanner.Scan() {
		res += scanner.Text()
	}
	return res
}
