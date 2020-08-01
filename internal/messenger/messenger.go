package messenger

import "net/textproto"

// Messenger is an interface for a generic messaging backend,
// for instance, e-mail, SMS etc.
type Messenger interface {
	Name() string
	Push(Message) error
	Flush() error
	Close() error
}

// Message is the message pushed to a Messenger.
type Message struct {
	From        string
	To          []string
	Subject     string
	Body        []byte
	Headers     textproto.MIMEHeader
	Attachments []Attachment
}

// Attachment represents a file or blob attachment that can be
// sent along with a message by a Messenger.
type Attachment struct {
	Name    string
	Header  textproto.MIMEHeader
	Content []byte
}

// MakeAttachmentHeader is a helper function that returns a
// textproto.MIMEHeader tailored for attachments, primarily
// email. If no encoding is given, base64 is assumed.
func MakeAttachmentHeader(filename, encoding string) textproto.MIMEHeader {
	if encoding == "" {
		encoding = "base64"
	}
	h := textproto.MIMEHeader{}
	h.Set("Content-Disposition", "attachment; filename="+filename)
	h.Set("Content-Type", "application/json; name=\""+filename+"\"")
	h.Set("Content-Transfer-Encoding", encoding)
	return h
}
