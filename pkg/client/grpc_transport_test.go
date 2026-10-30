package client

import (
	"context"
	"net"
	"testing"

	lumenvecpb "github.com/brma-tech/lumenvec-sdks/api/proto"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"google.golang.org/grpc/test/bufconn"
)

type transportVectorServer struct {
	lumenvecpb.UnimplementedVectorServiceServer
}

func (transportVectorServer) Search(_ context.Context, req *lumenvecpb.SearchRequest) (*lumenvecpb.SearchResponse, error) {
	if len(req.GetValues()) != 2 || req.GetTopK() != 1 {
		return nil, status.Error(codes.InvalidArgument, "expected two dimensions and k=1")
	}
	return &lumenvecpb.SearchResponse{
		Results: []*lumenvecpb.SearchResult{{Id: "transport-document", Distance: 0.25}},
	}, nil
}

// Exercise real gRPC HTTP/2 framing, not only mocked protobuf client methods,
// when upgrading the underlying golang.org/x/net transport dependency.
func TestGRPCTransportSearchRoundTrip(t *testing.T) {
	listener := bufconn.Listen(1 << 20)
	server := grpc.NewServer()
	lumenvecpb.RegisterVectorServiceServer(server, transportVectorServer{})
	go func() { _ = server.Serve(listener) }()
	t.Cleanup(func() {
		server.Stop()
		_ = listener.Close()
	})
	client, err := NewGRPCVectorClientWithDialer("passthrough:///transport-test", []grpc.DialOption{
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithContextDialer(func(ctx context.Context, _ string) (net.Conn, error) {
			return listener.DialContext(ctx)
		}),
	})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = client.Close() })
	results, err := client.SearchVector([]float64{1, 0}, 1)
	if err != nil {
		t.Fatalf("search over HTTP/2 failed: %v", err)
	}
	if len(results) != 1 || results[0].ID != "transport-document" || results[0].Distance != 0.25 {
		t.Fatalf("unexpected search result: %#v", results)
	}
	if _, err := client.SearchVector([]float64{1}, 1); status.Code(err) != codes.InvalidArgument {
		t.Fatalf("expected original gRPC error status, got %v", err)
	}
}
